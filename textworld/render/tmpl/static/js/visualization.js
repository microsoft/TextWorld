let state = $.parseJSON(document.currentScript.getAttribute('state').replace(/&quot;/g, '"'));
let template_path = document.currentScript.getAttribute('template_path');

const evtSrc = new EventSource("/subscribe");
evtSrc.onmessage = (e) => {
    state = JSON.parse(e.data)
    rerender()
}
const clicked = {};

let rerendered = false

const iconsMap = {
    anchor: 'Fixed.png',
    locked: 'Locked.png',
    closed: 'Unlocked.png',
    unlocked: 'Unlocked.png',
    cooked: 'Cooked.png',
    uncooked: 'Uncooked.png',
    chevron: 'Chevron.png',
};

// Label generators and helpers
function capitalize(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

function getMaxDepth(item) {
    if (item.contents.length == 0) {
        return 1;
    }
    var max = 0;
    for (let inner of item.contents) {
        var innerDepth = getMaxDepth(inner);
        if (innerDepth > max) {
            max = innerDepth;
        }
    }
    return 1 + max;
}

function getStaticIcon(icon) {
    const image = iconsMap[icon] || 'Object.png';
    return template_path + '/static/images/TextWorldIcons_' + image;
}

function getIcon(item) {
    let imageFile = '';
    switch (item.type) {
    case 'k':
        imageFile = 'Key.png';
        break;
    case 'P':
        imageFile = 'Player.png';
        break;
    case 'o':
        imageFile = 'Object.png';
        break;
    case 'f':
    case 'b':
        imageFile = 'Food.png';
        break;
    case 'c':
        if (item.ocl == 'open'){
            imageFile = 'ContainerOpen.png';
        } else if (item.ocl == 'closed' || item.ocl == 'locked') {
            imageFile = 'Container.png';
        } else {
            throw `Could not determine status ${item.ocl} of container ${item.name}`;
        }
        break;
    case 'd':
        if (item.ocl == 'open'){
            imageFile = 'DoorOpen.png';
        } else if (item.ocl == 'closed' || item.ocl == 'locked') {
            imageFile = 'Door.png';
        } else {
            throw `Could not determine status ${item.ocl} of door ${item.name}`;
        }
        break;
    case 's':
        imageFile = 'Supporter.png';
        break;
    default:
        imageFile = 'Object.png';
        break;
    }

    return template_path + '/static/images/TextWorldIcons_' + imageFile;
}


const opposite = (d) => {
    switch(d) {
    case 's':
        return 'n';
    case 'n':
        return 's';
    case 'e':
        return 'w';
    case 'w':
        return 'e';
    default:
        return null;
    }
};

// Helpers for finding starting/ending points based on direction
function calcDirection(connection, unit) {
    // WE NEED STATE OBJECT HERE
    const source = state.rooms.filter((r) => r.name == connection.source)[0];
    const dest = state.rooms.filter((r) => r.name == connection.target)[0];
    let diff = [dest.position[0] - source.position[0], dest.position[1] - source.position[1]];
    if (unit == 'dest') {
        diff = [source.position[0] - dest.position[0], source.position[1] - dest.position[1]];
    }
    if (diff[0] > 0) {
        return 'e'
    }
    else if (diff[0] < 0) {
        return 'w'
    }
    else if (diff[1] > 0) {
        return 'n'
    }
    else if (diff[1] < 0) {
        return 's'
    }
}
const calcShiftY = (dir, unit) => {
    switch(dir) {
    case 's':
        return unit;
    case 'n':
        return -unit;
    default:
        return 0;
    }
};

const calcShiftX = (dir, unit) => {
    switch(dir) {
    case 'e':
        return unit;
    case 'w':
        return -unit;
    default:
        return 0;
    }
};


function rerender() {
    const g = d3.select('g.wrapper');
    const transform = g.attr('transform');
    const scale = g.attr('scale');

    d3.select('svg').html('');
    d3.select('div.inventory-container').html('');
    Graph.render();
    const g2 = d3.select('g.wrapper');
    if (transform) {
        g2.attr('transform', transform);
    }

    if (scale) {
        g2.attr('scale', scale);
    }
}

function appendItemLabel(parent, p, n) {

    function hasItems(item) {
        return item.contents.length > 0 || clicked[item.name];
    }
    const rows = parent.selectAll('item')
        .data(p.data.items).enter()
        .append('tr')
        .attr('class', 'item')
        .attr('bgcolor', (item) => {
            if (item.highlight) {
                return '#ffffb2';
            }
        });


    const col = rows.append('td')
        .attr('class', 'item-text')
        .attr('sides', 'tr');

    const colContainer = col.append('div').attr('class', 'col-container');

    const colContainerLeft = colContainer.append('div').attr('class', 'col-container-left');

    colContainerLeft.append('img')
        .attr('class', 'icon')
        .attr('src', (item) => getIcon(item))
        .attr('scale', 'true');
    const colSpan = colContainerLeft.append('span')
        .style('line-height', '25px')
        .attr('class', 'item-span')
        .text((item) => {
            let description;
            if (!item.name) {
                description = item.type + item._infos;
            } else {
                description = item.name + item._infos;
            }
            return capitalize(description);
        });

    const colContainerRight = colContainer.filter((q) => hasItems(q))
        .append('div', 'col-container-right');

    const colContainerChevron = colContainerRight.append('img')
        .attr('class', (d) => {
            let className = 'anchor';
            if (clicked[d.name]) {
                className += ' rotate';
            }
            return className;
        })
        .attr('src', getStaticIcon('chevron'))
        .attr('scale', 'true');

    colSpan.filter((item) => !item.portable && item.type !== 'P')
        .append('img')
        .attr('class', 'anchor')
        .attr('src', getStaticIcon('anchor'))
        .attr('scale', 'true');

    col.each(function(q, i) {
        if (hasItems(q)) {
            var childData = {data: {items: q.contents}};
            const childTable = d3.select(this).append('table').attr('class', 'child-table');
            $(this).css('padding-bottom', 0)
            appendItemLabel(childTable, childData, i);
        }
    });

    rows.filter((item) => hasItems(item)).on('click', function(item) {

        if (clicked[item.name]) {
            item.contents = clicked[item.name];
            delete clicked[item.name];
        } else {
            clicked[item.name] = JSON.parse(JSON.stringify(item.contents));
            item.contents = [];
        }
        rerender();
    });
}

function calcRoomData(rooms) {

    return rooms.map(function(room) {
        const spreadX = 500;
        const spreadY = -500;
        return {
            x: room.position[0] * spreadX,
            y: room.position[1] * spreadY,
            data: room,
        };
    });
}

function renderRooms(room_data, g) {

    var nnodes = g.selectAll('node')
        .data(room_data)
        .enter().append('g')
        .attr('class', 'node')
        .attr('id', function(d) {
            return d.data.name;
        });

    var room = nnodes.append('foreignObject');
    var room_wrapper = room
        .append('xhtml:div');

    var room_table = room_wrapper.append('table')
        .attr('class', (d) => {
            let className = 'table room-table table-hover';
            for (const item of d.data.items) {
                if (item.type == 'P') {
                    className += ' current-room';
                }
            }
            return className;
        })
        .attr('sides', 'b')
        .attr('cellborder', '1')
        .attr('cellspacing', '0');

    var room_head = room_table.append('thead')
        .attr('class', (d) => {
            let className = 'thead-room';
            for (const item of d.data.items) {
                if (item.type == 'P') {
                    className += ' current-room-head';
                }
            }
            return className;
        })
        .append('tr')
        .append('th')
        .attr('class', 'room-name')
        .attr('sides', 'ltr')
        .attr('colspan', (d) => d.cols + 1);

    room_head.append('b')
        .attr('class', 'text')
        .text((d) => d.data.name);



    var room_body = room_table.append('tbody');
    room_body.each(appendItemsLabel);

    // we want to conditionally render our rectangles based on size of tables.
    var nodeWidth = room_table.nodes().map((n)=>n.getBoundingClientRect().width);

    room.attr('width', (r, i) => nodeWidth[i]);


    var nodeHeight = room_table.nodes().map((n)=>n.getBoundingClientRect().height);

    // set our rooms' size based on items.
    room.attr('height', (r, i) => nodeHeight[i]);

    nnodes.attr('transform', function(d, i) {
        const rect = this.getBoundingClientRect();
        const width = d.x - rect.width / 2;
        const height = d.y - rect.height / 2;
        room_data[i].x = width;
        room_data[i].y = height;
        return 'translate(' + width + ',' + height + ')';
    });
    return { room_g: nnodes, room_data: room_data };
}


function getDir(connection) {
    // this doesn't work with ambiguities in direction (special triangle case)
    const source = state.rooms.filter((r) => r.name == connection.src)[0];
    const dest = state.rooms.filter((r) => r.name == connection.dest)[0];
    let dir = '';
    for (const a of dest.base_room.attributes) {
        if (a.arguments[0].name == source.base_room.name) {
            dir = a.name;
        }
    }
    return dir;
}

function isImpossibleConnection(connection, room_data) {
    const source = room_data.find((d) => d.data.name == connection.src);
    const destination = room_data.find((d) => d.data.name == connection.dest);
    const dir = getDir(connection);
    return false
}

function renderEdges(edge_data, room_data, room_g, g) {
     // CREATING EDGES - we wrap our links with a wrapper g element

    const linkWrapper = g.selectAll('edgePath')
        .data(edge_data)
        .enter().append('g')
        .attr('class', 'edgeWrapper');

    const links = linkWrapper.append('line')
        .attr('class', 'edgePath')
        .attr('x1', function(l) {
            // calculating starting point
            var idx = 0;
            var sourceNode = room_g.filter(function(d, i) {
                if (d.data.name == l.source) {
                    idx = i;
                    return true;
                }
            }).node();
            const rect = sourceNode.getBoundingClientRect();
            const room_d = room_data.find((d) => d.data.name == l.source);
            var dir = calcDirection(l, 'source');
            var x = room_d.x + rect.width/2, y = room_d.y + rect.height / 2;

            d3.select(this).attr('y1', calcShiftY(dir, rect.height / 2) + y);
            return calcShiftX(dir, rect.width/2) + x;
        })
        .attr('x2', function(l) {
            // calculating ending point
            var idx = 0;
            var targetNode = room_g.filter(function(d, i) {
                if (d.data.name == l.target) {
                    idx = i;
                    return true;
                }
            }).node();
            const rect = targetNode.getBoundingClientRect();
            const room_d = room_data.find((d) => d.data.name == l.target);

            var dir = calcDirection(l, 'dest');
            var x = room_d.x + rect.width/2, y = room_d.y + rect.height / 2;
            d3.select(this).attr('y2', calcShiftY(dir, rect.height / 2) + y);
            return calcShiftX(dir, rect.width/2) + x;
        })
        .attr('fill', 'black')
        .attr('stroke', 'black');

    // Adding labels
    var lineg = linkWrapper.append('g');

    var edgeLabel = lineg.filter((n) => n.door)
        .append('foreignObject');

    const edgeLabelContainer = edgeLabel.append('xhtml:div')
        .attr('class', 'label-container');

    var edgeLabelElement = edgeLabelContainer
        .append('xhtml:table')
        .attr('class', 'table table-door')
        .attr('sides', 'b')
        .attr('bgcolor', 'white')
        .attr('cellborder', '1')
        .attr('cellspacing', '0');

    const edgeRow = edgeLabelElement.append('tr')
        .attr('class', 'door-row')
        .attr('bgcolor', (n) => {
            if (n.door.highlight) {
                return '#ffffb2';
            }
            return '';
        })
        .append('div')
        .attr('class', 'door-inner');

    edgeRow.append('span')
        .text((n) => capitalize(n.door.name))
        .attr('class', 'door-span');

    edgeRow.append('img')
        .attr('class', 'icon door-img-icon')
        .attr('width', 25)
        .attr('src', (n) => getIcon(n.door))
        .attr('scale', 'true');

    edgeRow.filter((n) => n.door.ocl !== 'open')
        .append('img')
        .attr('width', 25)
        .attr('class', 'icon door-img-icon')
        .attr('src', (n) => getStaticIcon(n.door.ocl))
        .attr('scale', 'true');


    const edgeTextHeight = edgeLabelElement.nodes().map((e) => e.firstChild.getBoundingClientRect().height);
    edgeLabel.attr('height', (e, i) => edgeTextHeight[i]);

    const edgeTextWidth = edgeLabelElement.nodes().map((e) => e.firstChild.getBoundingClientRect().width);
    edgeLabel.attr('width', (e, i) => edgeTextWidth[i]);

    lineg.filter((n) => n.door).attr('transform', function(d, i) {
        const n = links.filter((n) => n.door).nodes()[i];
        const x = (parseInt(n.getAttribute('x1')) + parseInt(n.getAttribute('x2')) - edgeTextWidth[i]) / 2;
        const y = (parseInt(n.getAttribute('y1')) + parseInt(n.getAttribute('y2')) - edgeTextHeight[i]) /2;
        return 'translate(' + x + ',' + y + ')';
    });

    return linkWrapper;
}


function renderInventory(inventory) {
    // Here we initialize the data for our nodes
    const inventory_node = [{x: 0, y:0, name: 'inventory', data: {items: inventory}}];

    // we must render the inventory first to position nodes around that
    const inventory_table = d3.select('div.inventory-container')
        .data(inventory_node)
        .append('table');

    inventory_table.attr('class', 'table table-hover')
        .attr('sides', 'b')
        .attr('cellborder', '1')
        .attr('cellspacing', '0');

    inventory_table.append('thead')
        .attr('class', 'thead-dark')
        .append('tr')
        .append('th')
        .append('b')
        .text('Inventory:');

    const inventory_body = inventory_table.append('tbody');
    inventory_body.each(appendItemsLabel);

    return inventory_table
}

function appendItemsLabel(p, j) {
    appendItemLabel(d3.select(this), p, 0);
}


const Graph = (function(window, d3, rerendered) {
    render();
    function render() {
        $('.history').html(state.history);
        if (state.history == "") {
            $('.history').html('<p class="objective-text">' + state.objective + '</p>');
        }
        if (state.command != "") {
            $("#command-scroll-div").scrollTop($("#command-scroll-div")[0].scrollHeight);
        }

        const svg = d3.select('#world');

        const inventory = renderInventory(state.inventory);

        // wrapper g for everything in svg
        const g = svg.append('g').attr('class', 'wrapper');
        let room_data = calcRoomData(state.rooms);

        const rooms = renderRooms(room_data, g);
        const room_g = rooms.room_g;
        room_data = rooms.room_data;

        const edge_data = state.connections.map(function(connection) {
            return {
                source: connection.src,
                target: connection.dest,
                door: connection.door,
                dir: getDir(connection),
                impossible: isImpossibleConnection(connection, room_data)
            };
        });

        const links = renderEdges(edge_data, room_data, room_g, g)


        svg.attr('width', g.node().getBBox().width);
        svg.attr('height', g.node().getBBox().height);


        const zoom = d3.zoom()
            .wheelDelta(() => {
                return -d3.event.deltaY * (d3.event.deltaMode ? 120 : 1) / 1000;
            })
            .scaleExtent([0.1, 3])
            .on('zoom', function() {
                g.attr('transform', d3.event.transform);
            });

        svg.call(zoom);

        // we check if it's our first rendering,
        // if it is we translate to center on the player.
        if (!rerendered) {
            const base = room_g.filter((d) => {
                for (const item of d.data.items) {
                    if (item.type == "P") {
                        return true;
                    }
                }
            });

            // for centering on 'P'
            // const translate = d3.select(base.node()).attr("transform").split('(')[1].split(')')[0].split(',');
            // const svgBBox = svg.node().getBoundingClientRect();
            // const x = svgBBox.width / 2 - parseInt(translate[0]) - 100;
            // const y = svgBBox.height / 2 - parseInt(translate[1]) - 100;
            // svg.call(zoom.transform, d3.zoomIdentity.translate(x, y));


            const width_ratio = svg.node().getBoundingClientRect().width / (g.node().getBoundingClientRect().width + 100);
            const height_ratio = svg.node().getBoundingClientRect().height / (g.node().getBoundingClientRect().height + 100);
            const ratio = width_ratio < height_ratio ? width_ratio : height_ratio;
            zoom.scaleBy(svg, ratio);
            const obj = $('.wrapper');
            const childPos = obj.offset();
            const parentPos = obj.parent().offset();

            const childOffset = {
                top: -childPos.top + 20,
                left: parentPos.left - childPos.left + 20
            };
            zoom.translateBy(svg, childOffset.left / ratio, childOffset.top / ratio)
            rerendered = true
        }

        // Currently not used - chrome doesn't support this.
        // const tableNode = $('.table-scroll');
        // tableNode.mouseenter(function() {
        //     if (this.scrollHeight !== this.clientHeight) {
        //         svg.on('.zoom', null);
        //     }
        // });
        //
        // tableNode.mouseleave(function() {
        //     svg.call(zoom);
        // });
    }

    return {
        render: render
    };
})(window, d3, rerendered);


const exportSVG = function(svg) {
    // first create a clone of our svg node so we don't mess the original one
    var clone = svg.cloneNode(true);
    // parse the styles
    parseStyles(clone);

    // create a doctype
    var svgDocType = document.implementation.createDocumentType('svg', "-//W3C//DTD SVG 1.1//EN", "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd");
    // a fresh svg document
    var svgDoc = document.implementation.createDocument('http://www.w3.org/2000/svg', 'svg', svgDocType);
    // replace the documentElement with our clone
    svgDoc.replaceChild(clone, svgDoc.documentElement);
    // get the data
    var svgData = (new XMLSerializer()).serializeToString(svgDoc);

    // now you've got your svg data, the following will depend on how you want to download it
    // e.g yo could make a Blob of it for FileSaver.js
    /*
    var blob = new Blob([svgData.replace(/></g, '>\n\r<')]);
    saveAs(blob, 'myAwesomeSVG.svg');
    */
    // here I'll just make a simple a with download attribute

    var a = document.createElement('a');
    a.href = 'data:image/svg+xml; charset=utf8, ' + encodeURIComponent(svgData.replace(/></g, '>\n\r<'));
    a.download = 'graph.svg';
    a.innerHTML = 'download the svg file';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
};

var parseStyles = function(svg) {
  var styleSheets = [];
  var i;
  // get the stylesheets of the document (ownerDocument in case svg is in <iframe> or <object>)
  var docStyles = svg.ownerDocument.styleSheets;

  // transform the live StyleSheetList to an array to avoid endless loop
  for (i = 0; i < docStyles.length; i++) {
    styleSheets.push(docStyles[i]);
  }

  if (!styleSheets.length) {
    return;
  }

  var defs = svg.querySelector('defs') || document.createElementNS('http://www.w3.org/2000/svg', 'defs');
  if (!defs.parentNode) {
    svg.insertBefore(defs, svg.firstElementChild);
  }
  svg.matches = svg.matches || svg.webkitMatchesSelector || svg.mozMatchesSelector || svg.msMatchesSelector || svg.oMatchesSelector;


  // iterate through all document's stylesheets
  for (i = 0; i < styleSheets.length; i++) {
    var currentStyle = styleSheets[i];

    var rules;
    try {
      rules = currentStyle.cssRules;
    } catch (e) {
      continue;
    }
    // create a new style element
    var style = document.createElement('style');
    // some stylesheets can't be accessed and will throw a security error
    var l = rules && rules.length;
    // iterate through each cssRules of this stylesheet
    for (var j = 0; j < l; j++) {
      // get the selector of this cssRules
      var selector = rules[j].selectorText;
      // probably an external stylesheet we can't access
      if (!selector) {
        continue;
      }

      // is it our svg node or one of its children ?
      if ((svg.matches && svg.matches(selector)) || svg.querySelector(selector)) {

        var cssText = rules[j].cssText;
        // append it to our <style> node
        style.innerHTML += cssText + '\n';
      }
    }
    // if we got some rules
    if (style.innerHTML) {
      // append the style node to the clone's defs
      defs.appendChild(style);
    }
  }

};

// Download button also not used
// $('button.save-svg').click(() => {
//     const svgData = document.getElementById('world')
//     exportSVG(svgData)
// });

window.addEventListener('resize', function() {
    rerender();
});
