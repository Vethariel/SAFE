from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import AppUser
from courses.models import Content, Course, Module
from enrollments.models import ContentProgress, CourseInscription, PathInscription
from learning_paths.models import CourseInPath, LearningPath
from teams.models import Team, TeamUser
from .services import (
    get_catalog_courses_for_user,
    get_contents_for_user_in_course,
    get_courses_for_user,
    get_courses_in_learning_path_for_user,
    get_paths_for_user,
)

User = get_user_model()


class RF5ServicesTests(TestCase):
    def setUp(self):
        self.analyst = User.objects.create_user(
            username="analyst",
            email="analyst@example.com",
            password="pass1234A!",
            role=AppUser.UserRole.ANALISTA_TH,
        )
        self.supervisor = User.objects.create_user(
            username="supervisor",
            email="supervisor@example.com",
            password="pass1234A!",
            role=AppUser.UserRole.SUPERVISOR,
        )
        self.collaborator = User.objects.create_user(
            username="collaborator",
            email="collaborator@example.com",
            password="pass1234A!",
            role=AppUser.UserRole.COLABORADOR,
        )

        self.course_active = Course.objects.create(
            name="Curso Activo",
            status=Course.CourseStatus.ACTIVE,
        )
        self.course_draft = Course.objects.create(
            name="Curso Borrador",
            status=Course.CourseStatus.DRAFT,
        )

        # Modular setup for content tests
        self.module = Module.objects.create(course=self.course_active, name="Módulo 1")
        self.content_a = Content.objects.create(
            module=self.module,
            title="Intro",
            description="c1",
            content_type=Content.ContentType.MATERIAL,
            block_type=Content.BlockType.TEXT,
            is_mandatory=False,
        )
        self.content_b = Content.objects.create(
            module=self.module,
            title="Checkpoint",
            description="c2",
            content_type=Content.ContentType.MATERIAL,
            block_type=Content.BlockType.TEXT,
            previous_content=self.content_a,
            is_mandatory=True,  # detiene el recorrido
        )
        self.content_a.next_content = self.content_b
        self.content_a.save(update_fields=["next_content"])

    def test_get_courses_for_user_analyst_sees_active(self):
        courses = get_courses_for_user(self.analyst)
        self.assertIn(self.course_active, courses)
        self.assertIn(self.course_draft, courses)

    def test_get_courses_for_user_supervisor_sees_team_courses(self):
        team = Team.objects.create(name="Equipo A", supervisor=self.supervisor)
        TeamUser.objects.create(team=team, app_user=self.collaborator)
        CourseInscription.objects.create(
            app_user=self.collaborator, course=self.course_active
        )

        courses = get_courses_for_user(self.supervisor)
        self.assertIn(self.course_active, courses)
        self.assertNotIn(self.course_draft, courses)

    def test_get_courses_for_user_collaborator_sees_own(self):
        CourseInscription.objects.create(
            app_user=self.collaborator, course=self.course_active
        )
        courses = get_courses_for_user(self.collaborator)
        self.assertIn(self.course_active, courses)
        self.assertNotIn(self.course_draft, courses)

    def test_get_contents_for_user_collaborator_sequential_until_mandatory(self):
        CourseInscription.objects.create(
            app_user=self.collaborator, course=self.course_active
        )
        visibles = get_contents_for_user_in_course(self.collaborator, self.course_active)
        self.assertEqual([self.content_a, self.content_b], list(visibles))

    def test_get_contents_for_user_supervisor_requires_team_inscription(self):
        # Supervisor without team inscription should see none
        visibles = get_contents_for_user_in_course(self.supervisor, self.course_active)
        self.assertEqual(0, len(visibles))

    def test_get_courses_in_learning_path_for_roles(self):
        path = LearningPath.objects.create(name="Ruta 1", status=LearningPath.PathStatus.ACTIVE)
        CourseInPath.objects.create(learning_path=path, course=self.course_active)

        # team setup
        team = Team.objects.create(name="Equipo B", supervisor=self.supervisor)
        TeamUser.objects.create(team=team, app_user=self.collaborator)
        CourseInscription.objects.create(
            app_user=self.collaborator, course=self.course_active
        )

        # analyst sees active course
        self.assertIn(
            self.course_active,
            get_courses_in_learning_path_for_user(self.analyst, path),
        )

        # supervisor sees because team enrolled
        self.assertIn(
            self.course_active,
            get_courses_in_learning_path_for_user(self.supervisor, path),
        )

        # collaborator sees because self enrolled
        self.assertIn(
            self.course_active,
            get_courses_in_learning_path_for_user(self.collaborator, path),
        )

    def test_get_paths_for_user_by_role(self):
        path = LearningPath.objects.create(name="Ruta A", status=LearningPath.PathStatus.ACTIVE)
        path_other = LearningPath.objects.create(name="Ruta B")

        PathInscription.objects.create(app_user=self.collaborator, learning_path=path)

        # team and supervisor inscription
        team = Team.objects.create(name="Equipo C", supervisor=self.supervisor)
        TeamUser.objects.create(team=team, app_user=self.collaborator)

        # analyst sees all
        analyst_paths = get_paths_for_user(self.analyst)
        self.assertIn(path, analyst_paths)
        self.assertIn(path_other, analyst_paths)

        # supervisor sees team inscriptions
        supervisor_paths = get_paths_for_user(self.supervisor)
        self.assertIn(path, supervisor_paths)
        self.assertNotIn(path_other, supervisor_paths)

        # collaborator sees own
        collaborator_paths = get_paths_for_user(self.collaborator)
        self.assertIn(path, collaborator_paths)
        self.assertNotIn(path_other, collaborator_paths)

    def test_catalog_courses_for_collaborator_exposes_progress(self):
        inscription = CourseInscription.objects.create(
            app_user=self.collaborator,
            course=self.course_active,
            progress=Decimal("25.00"),
            status=CourseInscription.InscriptionStatus.IN_PROGRESS,
        )
        ContentProgress.objects.create(
            content=self.content_a,
            course_inscription=inscription,
            is_completed=True,
        )

        cards = get_catalog_courses_for_user(self.collaborator)
        self.assertEqual(1, len(cards))
        card = cards[0]
        self.assertEqual(self.course_active, card.course)
        self.assertEqual(50.0, card.progress_percent)
        self.assertEqual(1, card.completed_contents)
        self.assertEqual(2, card.total_contents)
        self.assertEqual("Tu progreso", card.audience_label)

    def test_catalog_courses_for_supervisor_averages_team(self):
        teammate = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="pass1234A!",
            role=AppUser.UserRole.COLABORADOR,
        )
        team = Team.objects.create(name="Equipo Catalogo", supervisor=self.supervisor)
        TeamUser.objects.create(team=team, app_user=self.collaborator)
        TeamUser.objects.create(team=team, app_user=teammate)

        CourseInscription.objects.create(
            app_user=self.collaborator,
            course=self.course_active,
            progress=Decimal("20.00"),
            status=CourseInscription.InscriptionStatus.IN_PROGRESS,
        )
        second_inscription = CourseInscription.objects.create(
            app_user=teammate,
            course=self.course_active,
            progress=Decimal("40.00"),
            status=CourseInscription.InscriptionStatus.IN_PROGRESS,
        )
        # mark a single content completed by one teammate (1 of 2 contents across 2 users = 25%)
        ContentProgress.objects.create(
            content=self.content_a, course_inscription=second_inscription, is_completed=True
        )

        cards = get_catalog_courses_for_user(self.supervisor)
        self.assertEqual(1, len(cards))
        card = cards[0]
        self.assertEqual(2, card.inscription_count)
        self.assertEqual(25.0, card.progress_percent)
        self.assertEqual("Promedio del equipo", card.audience_label)

    def test_catalog_progress_uses_content_progress_counts(self):
        inscription = CourseInscription.objects.create(
            app_user=self.collaborator,
            course=self.course_active,
            progress=Decimal("0.00"),
            status=CourseInscription.InscriptionStatus.IN_PROGRESS,
        )
        ContentProgress.objects.create(
            content=self.content_a,
            course_inscription=inscription,
            is_completed=True,
        )
        cards = get_catalog_courses_for_user(self.collaborator)
        self.assertEqual(1, len(cards))
        self.assertEqual(50.0, cards[0].progress_percent)
