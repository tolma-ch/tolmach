(function () {
    'use strict';

    var module = angular.module('organizationsControllers', []);

    module.controller('organizationsCtrl', ['$scope', '$modal',
        function ($scope, $modal) {
            $scope.createNewOrg = function () {
                var modalInstance = $modal.open({
                    templateUrl: 'newOrganizationModal.html',
                    controller: 'NewOrganizationModalCtrl',
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

    module.controller('NewOrganizationModalCtrl', ['$scope', '$modalInstance', '$http',
        function ($scope, $modalInstance, $http) {
            $scope.name = generateRandomName();
            $scope.error = '';
            $scope.ok = function () {
                $scope.error = '';
                var data = {
                    'name': $scope.name.substring(0, 250)
                };
                $scope.busy = true;
                $http.post('/ajax/orgs/', data)
                    .success(function (data) {
                        location.href = '/orgs/' + data;
                    })
                    .error(function (data) {
                        $scope.error = data;
                        $scope.busy = false;
                        //$modalInstance.close();
                    });
            };

            $scope.createOrgAdvancedOptions = false;
            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        }
    ]);
}());