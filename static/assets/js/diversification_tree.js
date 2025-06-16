function diversification_tree(data)
{
    var treeData =  data


// ************** Generate the tree diagram	 *****************
var margin = {top: 20, right: 120, bottom: 20, left: 120},
	width = 960 - margin.right - margin.left,
	height = 500 - margin.top - margin.bottom;

var i = 0,
	duration = 750,
	root;

var tree = d3.layout.tree()
	.size([height, width]);

var diagonal = d3.svg.diagonal()
	.projection(function(d) { return [d.y, d.x]; });

var svg = d3.select('.diversification_tree').append('svg')
	.attr("width", "1150")
	.attr("height", height + margin.top + margin.bottom)
  .append("g")
	.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

root = treeData[0];
root.x0 = height / 2;
root.y0 = 0;

update(root);

d3.select(self.frameElement).style("height", "500px");

function update(source) {

  // Compute the new tree layout.
  var nodes = tree.nodes(root).reverse(),
	  links = tree.links(nodes);

  // Normalize for fixed-depth.
  nodes.forEach(function(d) { d.y = d.depth * 180; });

  // Update the nodes…
  var node = svg.selectAll("g.node")
	  .data(nodes, function(d) { return d.id || (d.id = ++i); });

  // Enter any new nodes at the parent's previous position.
  var nodeEnter = node.enter().append("g")
	  .attr("class", "node")
	  .attr("transform", function(d) { return "translate(" + source.y0 + "," + source.x0 + ")"; })
//	  .on("click", click);

  nodeEnter.append("circle")
	  .attr("r", 1e-6)
	  .style("fill", function(d) { return d._children ? "lightsteelblue" : "#fff"; });

  var circles = nodeEnter.selectAll("circle");

    /*****  tooltip *****/
        circles
        .append("title")
        .text(function(d) { return d.name; });
  var text_node = nodeEnter.append("text")
	  .attr("x", function(d) { return d.children || d._children ? -13 : 13; })
	  .attr("dy", ".35em")
	  .attr("text-anchor", function(d) { return d.children || d._children ? "middle" : "start"; })
	  .style("fill-opacity", 1e-6);

    text_node.append("tspan")
    .attr("x", function(d) { return 0; })
    .attr("dy", "20.256")
    .attr("fill", "#D0D2D6")
    .text(function(d) {

        var bracket1 = d.name.includes("(");
        var bracket2 = d.name.includes(")");
        console.log("bracket111--->", bracket1)
        console.log("bracket222--->", bracket2)

        if( bracket1 && bracket2)
        {
            console.log(d.name)
            return d.name
        }
        else
        {
            var node_name = d.name.split(" ")
            if(node_name.length >= 4)
            {
                if(node_name[2] == "&")
                {
                    return node_name[0] + " " + node_name[1] + " ... "
                }
                else
                {
                    return node_name[0] + " " + node_name[1] + " " + node_name[2] + " ..."
                }

            }
            else
            {
                return d.name
            }
        }
     })
  // Transition nodes to their new position.
  var nodeUpdate = node.transition()
	  .duration(duration)
	  .attr("transform", function(d) { return "translate(" + d.y + "," + d.x + ")"; });

  nodeUpdate.select("circle")
	  .attr("r", 10)
	  .style("fill", function(d) { return d._children ? "lightsteelblue" : "#fff"; });

  nodeUpdate.select("text")
	  .style("fill-opacity", 1);

  // Transition exiting nodes to the parent's new position.
  var nodeExit = node.exit().transition()
	  .duration(duration)
	  .attr("transform", function(d) { return "translate(" + source.y + "," + source.x + ")"; })
	  .remove();

  nodeExit.select("circle")
	  .attr("r", 1e-6);

  nodeExit.select("text")
	  .style("fill-opacity", 1e-6);

  // Update the links…
  var link = svg.selectAll("path.link")
	  .data(links, function(d)
	  {
	  		var width_link = d.target.same
	   		return d.target.id;
	});

  // Enter any new links at the parent's previous position.
  var link_up = link.enter().insert("path", "g")
	  .attr("style", function(d) {
	  	var width_value = d.target.same
	  	return "fill: none; stroke: steelblue; stroke-width:" + width_value +";"
	   });
	  link_up.attr("d", function(d) {
		var o = {x: source.x0, y: source.y0};
		return diagonal({source: o, target: o});
	  });

  // Transition links to their new position.
  link.transition()
	  .duration(duration)
	  .attr("d", diagonal);

  // Transition exiting nodes to the parent's new position.
  link.exit().transition()
	  .duration(duration)
	  .attr("d", function(d) {
		var o = {x: source.x, y: source.y};
		return diagonal({source: o, target: o});
	  })
	  .remove();

  // Stash the old positions for transition.
  nodes.forEach(function(d) {
	d.x0 = d.x;
	d.y0 = d.y;
  });
}

//// Toggle children on click.
function click(d) {
  if (d.children) {
	d._children = d.children;
	d.children = null;
  } else {
	d.children = d._children;
	d._children = null;
  }
  update(d);
}
}