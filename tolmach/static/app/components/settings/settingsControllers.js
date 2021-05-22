(function () {
    'use strict';

    var module = angular.module('settingsControllers', []);

    module.controller('settingsCtrl', ['$scope', '$http', 'localStorageService',
        function ($scope, $http, localStorageService) {
            $scope.userData = window['userData'];
            $scope.tmPercentage = $scope.userData.tmPercentage;

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
            $scope.saveProfile = function () {
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
                                    // $uibModalInstance.close(data);
                                });
                        } else {
                            // $uibModalInstance.close(data);
                        }
                        location.reload();
                    })
                    .error(function(data) {
                        $scope.error = data;
                        $scope.busy = false;
                        //$uibModalInstance.close();
                    });
            };

            $scope.textTab = 0;
            $scope.minFontSize = 10;
            $scope.maxFontSize = 26;
            $scope.increaseFontSize = 15;
            $scope.newFontSize = function () {
                console.log($scope.increaseFontSize);
                localStorageService.set('customFontSize', $scope.increaseFontSize);
            };

            $scope.updateTmPercentage = function () {
                console.log($scope.tmPercentage);
                $scope.busy = true;
                $scope.error = '';
                $http.post('/ajax/tm-percentage/', {'tmPercentage': $scope.tmPercentage})
                    .success(function (data) {
                        $scope.busy = false;
                    })
                    .error(function(data) {
                        $scope.error = data;
                        $scope.busy = false;
                        //$uibModalInstance.close();
                    });
            };
        }
    ]);

}());