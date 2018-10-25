(function () {
    'use strict';

    var module = angular.module('profileControllers', []);

    module.controller('ProfileCtrl', ['$scope', '$uibModal',
        function ($scope, $uibModal) {
            $scope.userData = window['userData'];
            $scope.editProfile = function () {
                var modalInstance = $uibModal.open({
                    templateUrl: 'editProfileModal.html',
                    controller: 'EditProfileModalCtrl',
                    size: 'md',
                    backdrop: 'static',
                    resolve: {
                        'userData': function () {
                            return $scope.userData;
                        }
                    }
                });

                modalInstance.result.then(function (userData) {
                    $scope.userData = userData;
                }, function () {

                });
            };
        }
    ]);

    var controller = module.controller('EditProfileModalCtrl', ['$scope', '$uibModalInstance', '$http', 'userData',
        function ($scope, $uibModalInstance, $http, userData) {
            $scope.cropper = {};
            $scope.cropper.sourceImage = null;
            $scope.cropper.croppedImage   = null;
            $scope.bounds = {};
            $scope.bounds.left = 0;
            $scope.bounds.right = 0;
            $scope.bounds.top = 0;
            $scope.bounds.bottom = 0;

            $scope.error = '';
            $scope.userData = userData;
            $scope.ok = function () {
                $scope.busy = true;
                $scope.error = '';
                $http.post('/ajax/user/', $scope.userData)
                    .success(function(data) {
                        if ($scope.cropper.croppedImage) {
                            $http.post('/ajax/user/', JSON.stringify($scope.cropper.croppedImage))
                                .success(function() {
                                    location.reload();
                                })
                                .error(function() {
                                    $scope.busy = false;
                                    $uibModalInstance.close(data);
                                });
                        } else {
                            $uibModalInstance.close(data);
                        }
                        location.reload();
                    })
                    .error(function(data) {
                        $scope.error = data;
                        $scope.busy = false;
                        //$uibModalInstance.close();
                    });
            };

            $scope.cancel = function () {
                $uibModalInstance.dismiss('cancel');
            };
        }
    ]);
}());