angular
    .module('tolmachApp')
    .component('handsontable', {
        bindings: {
            onUpdate: '&',
            sheet: '<'
        },
        templateUrl: 'handsontable.template.html',
        controller: ['$element', '$timeout', function ($element, $timeout) {
            var hot,
                cellRenderer = function (instance, td, row, col, prop, value, cellProperties) {
                    Handsontable.renderers.TextRenderer.apply(this, arguments);
                    //td.style.fontWeight = 'bold';
                    var color = matrix[row] && matrix[row][col];
                    if (color == 1) {
                        td.style.color = 'green';
                        td.style.background = '#CEC';
                    } else if (color == 2) {
                        td.style.color = 'blue';
                        td.style.background = '#CCE';
                    } else {
                        td.style.color = 'black';
                        td.style.background = '#FFF';
                    }
                },
                chr = function (codePt) {
                    if (codePt > 0xFFFF) {
                        codePt -= 0x10000;
                        return String.fromCharCode(0xD800 + (codePt >> 10), 0xDC00 + (codePt & 0x3FF));
                    }
                    return String.fromCharCode(codePt);
                },
                numToChar = function(number)    {
                    var numeric = number % 26;
                    var letter = chr(65 + numeric);
                    var number2 = parseInt(number / 26);
                    if (number2 > 0) {
                        return numToChar(number2) + letter;
                    } else {
                        return letter;
                    }
                },
                checkIntersection = function (coords1, coords2) {
                    if (Math.max(coords1[0], coords2[0]) <= Math.min(coords1[2], coords2[2])
                     && Math.max(coords1[1], coords2[1]) <= Math.min(coords1[3], coords2[3])) {
                        throw 'intersection';
                    }
                },
                matrix = [],
                fillRangeToMatrix = function (coords, color) {
                    for (var i = coords[0]; i <= coords[2]; i++) {
                        if (!matrix[i]) {
                            matrix[i] = [];
                        }
                        for (var j = coords[1]; j <= coords[3]; j++) {
                            matrix[i][j] = color;
                        }
                    }
                },
                fillMatrix = function () {
                    matrix = [];
                    for (var i in ranges) {
                        if (!ranges.hasOwnProperty(i)) {
                            continue;
                        }
                        var range = ranges[i];
                        fillRangeToMatrix(range.source.coords, 1);
                        fillRangeToMatrix(range.target.coords, 2);
                    }
                },
                activateNextRange = function (activeRange) {
                    var activeRangeIndex = ranges.indexOf(activeRange);
                    if (activeRangeIndex > -1 && ranges.hasOwnProperty(activeRangeIndex + 1)) {
                        var nextRange = ranges[activeRangeIndex + 1];
                        nextRange.active = true;
                        nextRange.source.active = true;
                    } else {
                        for (var i in ranges) {
                            if (!ranges.hasOwnProperty(i)) {
                                continue;
                            }
                            var range = ranges[i];
                            if (!range.source.coords) {
                                range.active = true;
                                range.source.active = true;
                                range.target.active = false;
                                return;
                            }
                            if (!range.target.coords) {
                                range.active = true;
                                range.target.active = true;
                                range.source.active = false;
                                return;
                            }
                            range.active = false;
                            range.source.active = false;
                            range.target.active = false;
                        }
                        ranges.push({
                            active: true,
                            source: {
                                coords: false,
                                text: '',
                                active: true
                            },
                            target: {
                                coords: false,
                                text: '',
                                active: false
                            }
                        });
                    }
                },
                ranges = [{
                    active: true,
                    source: {
                        coords: false,
                        text: '',
                        active: true
                    },
                    target: {
                        coords: false,
                        text: '',
                        active: false
                    }
                }];

            this.update = function () {
                this.onUpdate({value: ranges});
            };
            this.ranges = ranges;
            this.$onChanges = function(bindings) {
                var self = this;

                if (angular.isUndefined(bindings.ranges.previousValue) && angular.isDefined(bindings.ranges.currentValue)) {
                    ranges = bindings.ranges;
                    this.ranges = ranges;
                }
                if (bindings.sheet && !hot) {
                    var sheetContainer = $element.find('.sheet__container')[0];
                    $timeout (function () {
                        Handsontable.renderers.registerRenderer('cellRenderer', cellRenderer);
                        hot = new Handsontable(sheetContainer, {
                            data: self.sheet,
                            minSpareCols: 0,
                            minSpareRows: 0,
                            rowHeaders: true,
                            colHeaders: true,
                            contextMenu: true,
                            height: 500,
                            afterSelectionEnd: function (rowStart, columnStart, rowEnd, columnEnd) {
                                var coords = [rowStart, columnStart, rowEnd, columnEnd],
                                    text = numToChar(columnStart) + (rowStart + 1) + ":" +
                                           numToChar(columnEnd) + (rowEnd + 1),
                                    searchNext = false,
                                    activeRange;
                                try {
                                    for (var i in ranges) {
                                        if (!ranges.hasOwnProperty(i)) {
                                            continue;
                                        }
                                        var range = ranges[i];
                                        range.source.error = false;
                                        range.target.error = false;
                                        if (range.active) {
                                            activeRange = range;
                                            if (range.source.active) {
                                                checkIntersection(coords, range.target.coords);
                                            } else {
                                                checkIntersection(coords, range.source.coords);
                                            }
                                        } else {
                                            checkIntersection(coords, range.source.coords);
                                            checkIntersection(coords, range.target.coords);
                                        }
                                    }
                                    if (activeRange) {
                                        if (activeRange.source.active) {
                                            activeRange.source.coords = coords;
                                            activeRange.source.text = text;
                                            activeRange.source.active = false;
                                            activeRange.target.active = true;
                                        } else {
                                            activeRange.target.coords = coords;
                                            activeRange.target.text = text;
                                            activeRange.target.active = false;
                                            activeRange.active = false;
                                            activateNextRange(activeRange);
                                        }
                                    }
                                    fillMatrix();
                                    console.log(matrix);
                                } catch (e) {
                                    console.log('intersection');
                                }
                                hot.deselectCell();
                                self.update();
                                hot.render();
                            },
                            cells: function (row, col, prop) {
                                var cellProperties = {};
                                cellProperties.renderer = cellRenderer;
                                return cellProperties;
                            }
                        });
                    });
                }
            };
            var checkRanges = function () {
                for (var i in ranges) {
                    if (!ranges.hasOwnProperty(i)) {
                        continue;
                    }
                    var range = ranges[i];
                    if (!range.source.coords) {
                        range.source.error = true;
                        this.update();
                        return false;
                    }
                    if (!range.target.coords) {
                        range.target.error = true;
                        this.update();
                        return false;
                    }
                    range.active = false;
                    range.source.active = false;
                    range.target.active = false;
                }
                return true;
            };
            this.addRange = function () {
                if (!checkRanges()) {
                    return false;
                }
                this.ranges.push({
                    active: true,
                    source: {
                        coords: false,
                        text: '',
                        active: true
                    },
                    target: {
                        coords: false,
                        text: '',
                        active: false
                    }
                });
                this.update();
            };
            this.selectRange = function (range, input) {
                for (var i in ranges) {
                    if (!ranges.hasOwnProperty(i)) {
                        continue;
                    }
                    var someRange = ranges[i];
                    if (someRange === range) {
                        someRange.active = true;
                        someRange.source.active = !input;
                        someRange.target.active = input;
                    } else {
                        someRange.active = false;
                        someRange.source.active = false;
                        someRange.target.active = false;
                    }
                }
            };
            this.removeRange = function (range) {
                var index = ranges.indexOf(range);
                if (index > -1) {
                    ranges.splice(index, 1);
                    this.update();
                }
            }
        }]
    });