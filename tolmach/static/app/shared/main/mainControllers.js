(function () {
    'use strict';

    var module = angular.module('mainControllers', []);

    module.controller('mainCtrl', ['$scope', '$http', '$interval', '$modal', '$window', '$rootScope',
        function ($scope, $http, $interval, $modal, $window, $rootScope) {

            $rootScope.editPage = false;
            $rootScope.updateMessages = function () {
                $http.get('/ajax/message/').success(function (data) {
                    $scope.messages = data;
                }).error(function (data) {
                })
            };
            try {
                $scope.sidebarCollapsed = angular.fromJson(sessionStorage.sidebarCollapsed);
            } catch (e) {
                $scope.sidebarCollapsed = false;
            }
            $scope.toggleSidebar = function () {
                $scope.sidebarCollapsed = !$scope.sidebarCollapsed;
                sessionStorage.sidebarCollapsed = angular.toJson($scope.sidebarCollapsed);
            };
            $scope.showAllMessages = function () {
                var modalInstance = $modal.open({
                    templateUrl: 'allMessagesModal.html',
                    controller: 'AllMessagesModalCtrl',
                    size: 'md',
                    backdrop: 'static',
                    resolve: {}
                });

                modalInstance.result.then(function () {
                }, function () {
                });
            };
            $interval($rootScope.updateMessages, 5000);

            $scope.showSearch = false;
            $scope.globalSearch = function (query) {
                $scope.searchTextId = window['textId'] !== undefined ? window['textId'] : 0;
                $scope.searchTargetLang = window['translationTargetLang'] !== undefined ? window['translationTargetLang'] : 'none';
                return $http.get('/ajax/search', {params: {q: query,
                                                           textId: $scope.searchTextId,
                                                           targetLang: $scope.searchTargetLang}})
                    .then(function (response) {
                        return response.data;
                    });
            };
            $scope.onSearchSelect = function($item, $model, $label){
                $scope.$item = $item;
                $scope.$model = $model;
                $scope.$label = $label;
                console.log($scope.item);
                window.location = $scope.$item.link;

                // only needed when updating angular-routed urls including "#"
                if ($scope.$item.link.includes("#")) {
                    window.location.reload(true);
                }
            };

            $scope.redrawHelp = function () {
                if (!$scope.currentBlock) {
                    return;
                }
                var $block = $($scope.currentBlock),
                    params = $block.offset();
                params.width = $block.outerWidth();
                params.right = params.left + params.width;
                params.bottom = params.top + params.height;
                params.height = $block.outerHeight();
                $scope.helpBlockStyle1 = {
                    top: '0',
                    left: '0',
                    height: params.top + 'px',
                    right: '0'
                };
                $scope.helpBlockStyle2 = {
                    left: '0',
                    top: params.top + 'px',
                    width: params.left + 'px',
                    height: params.height + 'px'
                };
                $scope.helpBlockStyle3 = {
                    left: params.left + params.width + 'px',
                    top: params.top + 'px',
                    height: params.height + 'px',
                    right: 0
                };
                $scope.helpBlockStyle4 = {
                    left: '0',
                    top: params.top + params.height + 'px',
                    bottom: '0',
                    right: '0'
                };
                switch ($scope.position) {
                    case 'top':
                        $scope.helpBlockStyle1['z-index'] = 10001;
                        break;
                    case 'left':
                        $scope.helpBlockStyle2['z-index'] = 10001;
                        break;
                    case 'right':
                        $scope.helpBlockStyle3['z-index'] = 10001;
                        break;
                }
                $scope.helpCenterBlockStyle1 = {
                    top: params.top + 'px',
                    left: params.left + 'px',
                    height: params.height + 'px',
                    width: params.width + 'px'
                };
                var $body = $('body'),
                    textWidth = Math.min(300, $body.width()),
                    textRight = params.left + params.width,
                    textLeft = $scope.leftAlign ? Math.max(0, params.left - textWidth + 40) : Math.max(0, textRight - textWidth);
                textRight = Math.max(0, textLeft + textWidth);
                textWidth = textRight - textLeft;
                $scope.helpTextStyle1 = {
                    'bottom': '0',
                    'left': textLeft + 'px',
                    'width': textWidth + 'px'
                };
            };
            $scope.isFullscreenActive = false;
            $scope.toggleFullscreen = function () {
                if (screenfull.enabled) {
                    if (!screenfull.isFullscreen) {
                        screenfull.request();
                        $scope.isFullscreenActive = true;
                    } else {
                        screenfull.exit();
                        $scope.isFullscreenActive = false;
                    }
                }
            };
            function fullscreenchange() {
                if (screenfull.enabled) {
                    var elem = screenfull.element;

                    $('#status').text('Is fullscreen: ' + screenfull.isFullscreen);

                    if (elem) {
                        $('#element').text('Element: ' + elem.localName + (elem.id ? '#' + elem.id : ''));
                    }

                    if (!screenfull.isFullscreen) {
                        $('#external-iframe').remove();
                        document.body.style.overflow = 'auto';
                    }
                }
			}

            if (screenfull.enabled) {
                screenfull.on('change', fullscreenchange);
            }

			// Set the initial values
			fullscreenchange();
            $scope.beginHelpPresentation = function () {
                var event = $scope.$broadcast('helpPresentationStart');
                if (event.customized) {
                    return;
                }
                $scope.helpBlocks = $('.helped-block').toArray();
                $scope.currentBlock = $scope.helpBlocks.shift();
                $scope.clickBlock = false;
                $scope.leftAlign = false;
                $scope.position = 'top';
                $scope.hasNext = !!$scope.helpBlocks.length;
                if ($scope.currentBlock) {
                    $scope.helpText = $($scope.currentBlock).attr('help-text');
                    $scope.redrawHelp();
                    $scope.helpShow = true;
                } else {
                    $scope.closeHelpPresentation();
                }
            };
            $scope.closeHelpPresentation = function () {
                $scope.helpShow = false;
                $scope.helpBlocks = [];
                $scope.hasNext = false;
                $scope.currentBlock = null;
                $scope.clickBlock = false;
                $scope.leftAlign = false;
                $scope.position = 'top';
            };
            $scope.nextHelpStep = function () {
                $scope.currentBlock = false;
                $scope.helpText = false;
                $scope.hasNext = false;
                $scope.clickBlock = false;
                $scope.leftAlign = false;
                $scope.position = 'top';
                var event = $scope.$broadcast('helpPresentationNext');
                if (event.customized) {
                    return;
                }
                $scope.currentBlock = $scope.helpBlocks.shift();
                $scope.clickBlock = false;
                $scope.leftAlign = false;
                $scope.hasNext = !!$scope.helpBlocks.length;
                if ($scope.currentBlock) {
                    $scope.helpText = $($scope.currentBlock).attr('help-text');
                    $scope.redrawHelp();
                } else {
                    $scope.closeHelpPresentation();
                }
            };
            $scope.helpResize = function () {
                if ($scope.helpShow) {
                    $scope.redrawHelp();
                }
            };
            $scope.globalKeydown = function (event) {
                $scope.$broadcast('GlobalKeydown', event);
            };
            $scope.bodyClick = function (event) {
                $scope.$broadcast('GlobalClick', event);
            };

            $scope.showChatroom = false;
            $scope.toggleChat = function () {
                $scope.showChatroom = !$scope.showChatroom;
            };
            $scope.globalResize = function (window) {
                $scope.$broadcast('GlobalResize', window);
            };
            $scope.mouseup = function (event) {
                $scope.$broadcast('GlobalMouseup', event);
            };

            $scope.changeLanguage = function (language) {
                $http({
                    method: 'POST',
                    url: '/i18n/setlang/',
                    data: $.param({language: language}),
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'}
                }).success(function () {
                    $window.location.reload();
                })
            };
        }
    ]);

    module.controller('AllMessagesModalCtrl', ['$scope', '$modalInstance', '$http', '$rootScope',
        function ($scope, $modalInstance, $http, $rootScope) {
            $scope.error = '';
            $http.get('/ajax/message/all').success(function (data) {
                $scope.messages = data;
            }).error(function (data) {
            });
            $scope.readMessage = function (message) {
                if (message.was_read !== true) {
                    $http.post('/ajax/message/', {id: message.id}).success(function (data) {
                        for (var i in $scope.messages) {
                            if ($scope.messages[i].id == message.id) {
                                $scope.messages[i].was_read = true;
                            }
                        }
                        $rootScope.updateMessages();
                    }).error(function (data) {
                    })
                }
            };

            $scope.cancel = function () {
                $modalInstance.dismiss('cancel');
            };
        }
    ]);
}());