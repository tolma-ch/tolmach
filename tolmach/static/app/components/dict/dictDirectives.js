(function () {
    'use strict';

    var module = angular.module('dictDirectives', []);

    module.directive('focusOn', ['$timeout', function($timeout) {
        return {
            restrict : 'A',
            link : function($scope,$element,$attr) {
                $scope.$watch($attr.focusOn,function(_focusVal) {
                    $timeout(function() {
                        //_focusVal ? $element[0].focus() : $element[0].blur();
                        if (_focusVal) {
                            $element[0].focus();
                            $element[0].setSelectionRange(0, $element[0].value.length);
                        } else {
                            $element[0].blur();
                        }
                    });
                });
            }
        }
    }]);
}());