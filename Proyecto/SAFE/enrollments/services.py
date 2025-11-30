from dataclasses import dataclass
from typing import List, Optional

from django.db.models import Count, Prefetch, Q

from accounts.models import AppUser
from courses.models import Course, Content, Module
from enrollments.models import ContentProgress, CourseInscription
from learning_paths.models import LearningPath
from teams.models import TeamUser


@dataclass
class CatalogCourseCard:
    """Course data enriched for the catalog cards."""

    course: Course
    status_label: str
    progress_percent: Optional[float]
    completed_contents: int
    total_contents: int
    modules_count: int
    audience_label: str
    inscription_count: int


def _get_team_member_ids(supervisor: AppUser):
    """Return the ids of the users under a supervisor."""
    return TeamUser.objects.filter(team__supervisor=supervisor).values_list(
        "app_user_id", flat=True
    )


def get_courses_for_user(user: AppUser):
    """
    Return the courses visible to a user according to their role.
    """

    # 1. Analista TH -> all active courses
    if user.role == AppUser.UserRole.ANALISTA_TH:
        return Course.objects.filter(
            status__in=[Course.CourseStatus.ACTIVE, Course.CourseStatus.DRAFT]
        )

    # 2. Supervisor -> courses where someone in their team is enrolled
    if user.role == AppUser.UserRole.SUPERVISOR:
        team_members = _get_team_member_ids(user)

        if not team_members:
            return Course.objects.none()

        return (
            Course.objects.filter(
                inscriptions__app_user_id__in=team_members,
                status=Course.CourseStatus.ACTIVE,
            )
            .distinct()
        )

    # 3. Colaborador -> own courses
    if user.role == AppUser.UserRole.COLABORADOR:
        return (
            Course.objects.filter(
                inscriptions__app_user=user,
                status=Course.CourseStatus.ACTIVE,
            )
            .distinct()
        )

    return Course.objects.none()


def get_contents_for_user_in_course(user: AppUser, course: Course):
    """
    Determine which contents are visible for a given user inside a course.
    """
    # helper for collaborator progress by modules
    def _completed_ids_for(user: AppUser, course_obj: Course):
        try:
            inscription = CourseInscription.objects.get(app_user=user, course=course_obj)
        except CourseInscription.DoesNotExist:
            return set()
        return set(
            ContentProgress.objects.filter(
                course_inscription=inscription, is_completed=True
            ).values_list("content_id", flat=True)
        )

    # 1. Analista TH: can see everything
    if user.role == AppUser.UserRole.ANALISTA_TH:
        return Content.objects.filter(module__course=course)

    # 2. Supervisor: can see everything only if their team is enrolled
    if user.role == AppUser.UserRole.SUPERVISOR:
        team_members = _get_team_member_ids(user)

        if CourseInscription.objects.filter(
            app_user_id__in=team_members, course=course
        ).exists():
            return Content.objects.filter(module__course=course)

        return Content.objects.none()

    # 3. Colaborador: sequential navigation based on course contents
    if user.role == AppUser.UserRole.COLABORADOR:
        if not CourseInscription.objects.filter(app_user=user, course=course).exists():
            return Content.objects.none()

        completed_ids = _completed_ids_for(user, course)
        modules = list(
            Module.objects.filter(course=course)
            .prefetch_related("contents")
            .order_by("id")
        )

        unlocked_module_ids = set()
        previous_completed = True  # first module unlocked

        for module in modules:
            if previous_completed:
                unlocked_module_ids.add(module.id)

            module_content_ids = [c.id for c in module.contents.all()]
            module_completed = not module_content_ids or all(
                content_id in completed_ids for content_id in module_content_ids
            )
            previous_completed = previous_completed and module_completed

        return (
            Content.objects.filter(
                module__course=course, module_id__in=unlocked_module_ids
            )
            .order_by("module_id", "id")
        )

    return Content.objects.none()


def get_courses_in_learning_path_for_user(user: AppUser, path: LearningPath):
    """
    Return the courses inside a learning path that are visible for the user.
    """

    # 1. Analista TH -> all active courses inside the path
    if user.role == AppUser.UserRole.ANALISTA_TH:
        return Course.objects.filter(
            in_paths__learning_path=path,
            status__in=[Course.CourseStatus.ACTIVE, Course.CourseStatus.DRAFT],
        ).distinct()

    # 2. Supervisor -> courses in the path where their team is enrolled
    if user.role == AppUser.UserRole.SUPERVISOR:
        team_members = _get_team_member_ids(user)

        if not team_members:
            return Course.objects.none()

        return (
            Course.objects.filter(
                in_paths__learning_path=path,
                inscriptions__app_user_id__in=team_members,
                status=Course.CourseStatus.ACTIVE,
            )
            .distinct()
        )

    # 3. Colaborador -> courses in the path where they are enrolled
    if user.role == AppUser.UserRole.COLABORADOR:
        return (
            Course.objects.filter(
                in_paths__learning_path=path,
                inscriptions__app_user=user,
                status=Course.CourseStatus.ACTIVE,
            )
            .distinct()
        )

    return Course.objects.none()


def get_paths_for_user(user: AppUser):
    """
    Return the learning paths visible to the user using only PathInscription.
    """

    # 1. Analista TH -> all paths
    if user.role == AppUser.UserRole.ANALISTA_TH:
        return LearningPath.objects.all()

    # 2. Supervisor -> paths where their team is enrolled
    if user.role == AppUser.UserRole.SUPERVISOR:
        return _get_paths_for_supervisor(user)

    # 3. Colaborador -> paths where they are enrolled
    if user.role == AppUser.UserRole.COLABORADOR:
        return _get_paths_for_colaborador(user)

    return LearningPath.objects.none()


def _get_paths_for_colaborador(user: AppUser):
    """Helper: paths where the collaborator is enrolled."""
    return LearningPath.objects.filter(inscriptions__app_user=user).distinct()


def _get_paths_for_supervisor(user: AppUser):
    """Helper: paths where someone in the supervisor's team is enrolled."""
    team_members_ids = _get_team_member_ids(user)

    if not team_members_ids:
        return LearningPath.objects.none()

    return LearningPath.objects.filter(
        inscriptions__app_user_id__in=team_members_ids
    ).distinct()


def _build_inscriptions_prefetch(user: AppUser):
    """Return a Prefetch with the inscriptions relevant for the viewer."""
    if user.role == AppUser.UserRole.COLABORADOR:
        completed_prefetch = Prefetch(
            "content_progress",
            queryset=ContentProgress.objects.filter(is_completed=True),
            to_attr="completed_progress",
        )
        inscriptions_qs = CourseInscription.objects.filter(app_user=user).prefetch_related(
            completed_prefetch
        )
        return Prefetch(
            "inscriptions", queryset=inscriptions_qs, to_attr="visible_inscriptions"
        )

    if user.role == AppUser.UserRole.SUPERVISOR:
        team_members_ids = _get_team_member_ids(user)
        base_qs = CourseInscription.objects.filter(app_user_id__in=team_members_ids)

        completed_prefetch = Prefetch(
            "content_progress",
            queryset=ContentProgress.objects.filter(is_completed=True),
            to_attr="completed_progress",
        )
        inscriptions_qs = base_qs.prefetch_related(completed_prefetch)
        return Prefetch(
            "inscriptions", queryset=inscriptions_qs, to_attr="visible_inscriptions"
        )

    return None


def _build_catalog_card_for_course(
    course: Course, user: AppUser
) -> CatalogCourseCard:
    """Assemble the data required by the catalog card template."""
    inscriptions: List[CourseInscription] = getattr(
        course, "visible_inscriptions", []
    ) or []
    total_contents = getattr(course, "contents_count", 0) or 0
    modules_count = getattr(course, "modules_count", 0) or 0

    if user.role == AppUser.UserRole.COLABORADOR:
        inscription = inscriptions[0] if inscriptions else None
        completed_contents = len(getattr(inscription, "completed_progress", []) or []) if inscription else 0
        progress_percent = (
            (completed_contents / total_contents) * 100 if total_contents else 0.0
        )
        status_label = (
            inscription.get_status_display() if inscription else "No inscrito"
        )
        audience_label = "Tu progreso"
        inscription_count = 1 if inscription else 0

    elif user.role == AppUser.UserRole.SUPERVISOR:
        inscription_count = len(inscriptions)
        completed_contents = sum(
            len(getattr(ins, "completed_progress", []) or []) for ins in inscriptions
        )
        max_possible = total_contents * inscription_count
        progress_percent = (completed_contents / max_possible * 100) if max_possible else 0.0
        status_label = (
            "Equipo inscrito" if inscription_count else "Sin equipo inscrito"
        )
        audience_label = "Promedio del equipo"

    elif user.role == AppUser.UserRole.ANALISTA_TH:
        progress_percent = None
        completed_contents = 0
        status_label = course.get_status_display()
        audience_label = "Disponible"
        inscription_count = 0

    else:
        progress_percent = None
        completed_contents = 0
        status_label = course.get_status_display()
        audience_label = "Disponible"
        inscription_count = 0

    return CatalogCourseCard(
        course=course,
        status_label=status_label,
        progress_percent=progress_percent,
        completed_contents=completed_contents,
        total_contents=total_contents,
        modules_count=modules_count,
        audience_label=audience_label,
        inscription_count=inscription_count,
    )


def get_catalog_courses_for_user(user: AppUser) -> List[CatalogCourseCard]:
    """
    Build catalog-friendly course data including inscription/progress visibility by role.
    """
    courses_qs = (
        get_courses_for_user(user)
        .annotate(
            modules_count=Count("modules", distinct=True),
            contents_count=Count("modules__contents", distinct=True),
        )
        .order_by("-created_at")
    )

    prefetch = _build_inscriptions_prefetch(user)
    if prefetch is not None:
        courses_qs = courses_qs.prefetch_related(prefetch)

    return [_build_catalog_card_for_course(course, user) for course in courses_qs]


def get_course_progress(user: AppUser, course: Course):
    """
    Return total/complete counts and percent for a user in a course using ContentProgress.
    """
    total_contents = (
        Content.objects.filter(module__course=course).distinct().count()
    )
    completed_contents = 0

    try:
        inscription = CourseInscription.objects.get(app_user=user, course=course)
    except CourseInscription.DoesNotExist:
        inscription = None

    if inscription:
        completed_contents = ContentProgress.objects.filter(
            course_inscription=inscription, is_completed=True
        ).count()

    percent = (completed_contents / total_contents * 100) if total_contents else 0
    return {
        "total": total_contents,
        "completed": completed_contents,
        "percent": percent,
        "inscription": inscription,
    }
