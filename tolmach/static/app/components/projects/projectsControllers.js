(function () {
    'use strict';

    var module = angular.module('projectsControllers', []);

    module.controller('projectsCtrl', ['$scope', '$modal',
        function ($scope, $modal) {
            $scope.startNewProject = function () {
                var modalInstance = $modal.open({
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

        }
    ]);

    module.controller('NewProjectModalCtrl', ['$scope', '$modalInstance', '$http',
        function ($scope, $modalInstance, $http) {
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
                        //$modalInstance.close();
                    });
            };

            $scope.addProjectAdvancedOptions = false;
            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        }
    ]);
}());