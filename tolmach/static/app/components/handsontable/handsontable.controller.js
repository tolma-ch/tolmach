angular
    .module('tolmachApp')
    .component('handsontable', {
        bindings: {
            onUpdate: '&',
            sheet: '<'
        },
        templateUrl: '/static/app/components/handsontable/handsontable.template.html',
        controller: ['$element', '$timeout', function ($element, $timeout) {
            var hot,
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
                ranges = [];
            this.update = function () {
                this.onUpdate({value: ranges});
            };
            this.ranges = ranges;
            this.$onChanges = function(bindings) {
                var self = this;
                if (bindings.sheet && !hot) {
                    var sheetContainer = $element.find('.sheet__container')[0];
                    //$timeout (function () {
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
                                    searchNext = false;
                                for (var i in ranges) {
                                    if (!ranges.hasOwnProperty(i)) {
                                        continue;
                                    }
                                    var range = ranges[i];
                                    if (searchNext) {
                                        range.active = true;
                                        range.source.active = true;
                                        range.target.active = false;
                                        searchNext = false;
                                        break;
                                    }
                                    if (range.active) {
                                        if (range.source.active) {
                                            range.source.coords = coords;
                                            range.source.text = text;
                                            range.source.error = false;
                                            range.source.active = false;
                                            range.target.active = true;
                                            break;
                                        } else {
                                            range.target.coords = coords;
                                            range.target.text = text;
                                            range.target.error = false;
                                            range.target.active = false;
                                            range.active = false;
                                            searchNext = true;
                                        }
                                    }
                                }
                                this.update();
                                console.log(text);
                                hot.deselectCell();
                            }
                        });
                    //});
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
                        range.active = true;
                        range.source.active = !input;
                        range.target.active = input;
                    } else {
                        range.active = false;
                        range.source.active = false;
                        range.target.active = false;
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