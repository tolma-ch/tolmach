(function () {
    'use strict';

    var module = angular.module('organizationsControllers', []);

    module.controller('organizationsCtrl', ['$scope', '$modal', '$http',
        function ($scope, $modal, $http) {
            $scope.activeTab = window['activeTab'];
            $scope.orgId = window.userData['orgId'];
            $scope.members = [];

            $scope.reloadMembers = function () {
                $http.get('/ajax/orgs/members/', {params: {organization: $scope.orgId}})
                .then(function (response) {
                    $scope.members = response.data;
                });
            };
            if ($scope.activeTab === "members") {
                 $scope.reloadMembers();
            }

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

                modalInstance.result.then(function (member) {
                    $scope.members.push(member);
                }, function () {
                });
            };

            $scope.changeAdminStatus = function(member) {
                if(typeof(member.status) === "boolean") {
                    console.log(member.status);
                    var data = {
                        'organization': window.userData['orgId'],
                        'user': member.id,
                        'is_admin': member.status
                    };
                    $scope.busy = true;
                    $http.post('/ajax/orgs/members/', data)
                        .success(function (member) {
                            $scope.reloadMembers();
                            $scope.busy = false;
                        })
                        .error(function (data) {
                            console.log(data);
                            $scope.busy = false;
                        });
                }
            };

            $scope.removeOrgParticipant = function (member) {
                var data = {
                    'organization': $scope.orgId,
                    'user': member.id
                };
                $scope.busy = true;
                $http.delete('/ajax/orgs/members/', {params: data})
                    .success(function () {
                        var i = $scope.members.indexOf(member);
                        if (i > -1) {
                            delete $scope.members.splice(i, 1);
                        }
                        $scope.busy = false;
                    })
                    .error(function (data) {
                        $scope.error = data;
                        $scope.busy = false;
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

    module.controller('AddOrgParticipantModalCtrl', ['$scope', '$modalInstance', '$http', '$window',
        function ($scope, $modalInstance, $http, $window) {
            $scope.getUsers = function (query) {
                return $http.get('/ajax/get-users', {params: {q: query}})
                    .then(function (response) {
                        return response.data;
                    });
            };
            $scope.ok = function () {
                $scope.error = '';
                var data = {
                    'organization': window.userData['orgId'],
                    'user': $scope.user.id
                };
                $scope.busy = true;
                $http.post('/ajax/orgs/members/', data)
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