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

            $scope.addOrgParticipant = function () {
                var modalInstance = $modal.open({
                    templateUrl: 'addOrgParticipantModal.html',
                    controller: 'AddOrgParticipantModalCtrl',
                    size: 'md',
                    backdrop: 'static',
                    resolve: {}
                });

                modalInstance.result.then(function (participant) {
                    // $scope.participants.push(participant);
                    $window.location.reload();
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

    module.controller('AddOrgParticipantModalCtrl', ['$scope', '$modalInstance', '$http',
        function ($scope, $modalInstance, $http) {
            $scope.getUsers = function (query) {
                return $http.get('/ajax/get-users', {params: {q: query}})
                    .then(function (response) {
                        return response.data;
                    });
            };
            $scope.ok = function () {
                $scope.error = '';
                var data = {
                    'project': window['projectId'],
                    'user': $scope.user.id
                };
                $scope.busy = true;
                $http.post('/ajax/participant/', data)
                    .success(function (participant) {
                        $modalInstance.close(participant);
                        $scope.busy = false;
                    })
                    .error(function (data) {
                        $scope.error = data;
                        $scope.busy = false;
                    });
            };

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        }
    ]);
}());