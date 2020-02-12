'use strict';

angular.module('ngClickCopy', [])
.service('ngCopy', ['$window', function ($window) {
	var body = angular.element($window.document.body);
	var textarea = angular.element('<textarea/>');
	textarea.css({
		position: 'fixed',
		opacity: '0'
	});

	return function (toCopy) {
		textarea.val(toCopy);
		body.append(textarea);
		textarea[0].select();

		var succeed = false;

		try {
			var successful = document.execCommand('copy');
			if (!successful) throw successful;
			succeed = true;
		} catch (err) {
			window.prompt("Copy to clipboard: Ctrl+C, Enter", toCopy);
		}

		textarea.remove();

		return succeed;
	}
}])
.directive('ngClickCopy', ['ngCopy', function (ngCopy) {
	return {
		restrict: 'A',
		link: function (scope, element, attrs) {
			element.bind('mousedown', function (e) {
				if (e.which != 1)
				{
					return;
				}
				e.originalEvent.preventDefault();
				var prevFocus = document.activeElement;
				if (ngCopy(attrs.ngClickCopy))
				{
					if (attrs.ngClickCopyMessage)
					{
						var tooltip = angular.element('<div class="copied-tooltip">'+attrs.ngClickCopyMessage+'</div>');
						tooltip.css({
							position: 'absolute',
							top: '0',
							right: '0',
							marginTop: '0',
							opacity: 1,
							pointerEvents: 'none',
							userSelect: 'none',
							textShadow: '0 0 1px rgba(0, 0, 0, .16)',
							userSelect: 'none'
						});
						angular.element(e.currentTarget.parentElement).after(tooltip);
						setTimeout(() => {
							tooltip.css({
								marginTop: '-35px',
								opacity: '0'
							});
						}, 10);
						setTimeout(() => {
							tooltip.remove();
						}, 510);
					}
				}
				if (prevFocus) {
					prevFocus.focus();
				}
			});
		}
	}
}]);