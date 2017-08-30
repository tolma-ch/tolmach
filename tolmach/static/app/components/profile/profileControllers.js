(function () {
    'use strict';

    var module = angular.module('profileControllers', []);

    module.controller('ProfileCtrl', ['$scope', '$modal',
        function ($scope, $modal) {
            $scope.userData = window['userData'];
            $scope.editProfile = function () {
                var modalInstance = $modal.open({
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

    var controller = module.controller('EditProfileModalCtrl', ['$scope', '$modalInstance', '$http', 'userData',
        function ($scope, $modalInstance, $http, userData) {
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
                                    $modalInstance.close(data);
                                });
                        } else {
                            $modalInstance.close(data);
                        }
                    })
                    .error(function(data) {
                        $scope.error = data;
                        $scope.busy = false;
                        //$modalInstance.close();
                    });
            };

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        }
    ]);
}());