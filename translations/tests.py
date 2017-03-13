# -*- coding: utf-8 -*-

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from translations import views_ajax
from translations.models import Project
import json


class CreateProjectTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='jacob', email='jacob@gmail.com', password='top_secret')

    def test_create_project(self):
        request = self.factory.post('/api/project-create/',
                                    data=json.dumps({'name': 4321, 'description': "ololo", 'type': "public"}),
                                    content_type='application/json')
        request.user = self.user
        response = views_ajax.create_project_ajax(request)

        all_user_projects = Project.objects.filter(manager=self.user)

        self.assertEqual(len(all_user_projects), 1)
        self.assertEqual(response.status_code, 200)

    def test_add_text_to_project(self):
        project = Project.objects.get(manager=self.user, name=4321)
        data = json.dumps({"project":project.id,
                           "title":"French test",
                           "subject":1,
                           "sourceLang":7,
                           "targetLang":2,
                           "textBody":"De son côté, Clay désire toujours récupérer le marteau: il recrute des Nomades, Frankie, Greg et Gogo, auxquels il promet de l'argent en échange d'agressions qu'ils devront perpétrer à Charming. L'objectif est de déstabiliser Jax et de faire porter la suspicion sur le club. Mais Rita, la femme du chef de la police Eli Roosevelt, est accidentellement tuée lors de l'une de ces attaques. L'étau se resserre autour de Clay: il est soupçonné par Unser, et encore plus fortement par Jax et Bobby, d'autant plus lorsque Frankie le balance avant d'être tué. Eli et Jax concluent un deal: Jax doit livrer Frankie vivant au policier, et Eli lui révélera le nom de la taupe au sein du MC. Mais Jax ne peut empêcher la mort de Frankie. Eli est furieux en découvrant le cadavre de Frankie, mais Jax lui explique qu'il va trouver des preuves pour incriminer Clay, le vrai responsable. Jax, devant le refus d'Eli de livrer la taupe, explique qu'il la connaît déjà, par déduction: il s'agit de Juice."})

        request = self.factory.post('/api/text/', data=data, content_type='application/json')
        request.user = self.user

        response = views_ajax.text_ajax(request)

        self.assertEqual(response.status_code, 200)
