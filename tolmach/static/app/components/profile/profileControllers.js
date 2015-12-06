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
            $scope.error = '';
            $scope.userData = userData;
            $scope.imageCropResult = null;
            $scope.showImageCropper = true;
            $scope.imageCropStep = 1;
            $scope.blah = 1;
            $scope.$watch('imageCropResult', function(newVal) {
                $scope.blah++;
                if (newVal) {
                    console.log('imageCropResult', newVal);
                }
                return newVal;
            });
            $scope.ok = function () {
                $scope.busy = true;
                $scope.error = '';
                $http.post('/api/user/', $scope.userData)
                    .success(function(data) {
                        if ($scope.imageCropResult) {
                            $http.post('/api/user/', JSON.stringify($scope.imageCropResult))
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