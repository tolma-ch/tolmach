(function () {
    'use strict';

    var module = angular.module('projectsControllers', []);

    module.controller('projectsCtrl', ['$scope', '$uibModal', '$http', '$location',
        function ($scope, $uibModal, $http, $location) {
            $scope.page = parseInt($location.search().page ? $location.search().page : 1) || 1;
            $scope.projects = {};
            $scope.busy = false;

            var updateProjects = function () {
                $scope.busy = true;
                $http.get('/ajax/projects/' + window['active_tab'] + '/?page=' + $scope.page)
                    .then(function (response) {
                        $scope.projects = response.data;
                        $scope.busy = false;
                });
            };
            updateProjects();
            console.log($scope.projects);
            $scope.startNewProject = function () {
                var modalInstance = $uibModal.open({
                    templateUrl: 'newProjectModal.html',
                    controller: 'NewProjectModalCtrl',
                    size: 'md',
                    backdrop: 'static',
                    resolve: {}
                });

                modalInstance.result.then(function () {
                }, function () {
                });
            };

            $scope.changePage = function (page_num) {
                if ($scope.busy) {
                    return;
                }
                if (1 <= page_num <= $scope.projects.paginator.num_pages) {
                    $scope.page = page_num;
                    updateProjects();
                    $location.search('page', $scope.page).replace();
                }
            };

        }
    ]);

    module.controller('NewProjectModalCtrl', ['$scope', '$uibModalInstance', '$http',
        function ($scope, $uibModalInstance, $http) {
            $scope.name = generateRandomName();
            $scope.error = '';
            $scope.type = 'private';
            $scope.ok = function () {
                $scope.error = '';
                var data = {
                    'name': $scope.name.substring(0, 250),
                    'description': $scope.description || " ",
                    'type': $scope.type,
                    'source_lang': $scope.source_lang,
                    'target_lang': $scope.target_lang,
                    'org_id': window.userData['orgId'] || 0
                };
                $scope.busy = true;
                $http.post('/ajax/project-create/', data)
                    .success(function (data) {
                        location.href = '/project/' + data;
                    })
                    .error(function (data) {
                        $scope.error = data;
                        $scope.busy = false;
                        //$uibModalInstance.close();
                    });
            };

            $scope.addProjectAdvancedOptions = false;
            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }
    ]);
}());