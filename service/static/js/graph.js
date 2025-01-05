const svg = d3.select("#viz");
const width = +svg.attr("width");
const height = +svg.attr("height");

// Margin or padding if you want some space around the grid
const margin = 40;

// Depth indicator element
const depthIndicator = document.getElementById("depth-indicator");

// Initialize depth
let currentDepth = 0;

// Fetch initial data once the page loads
init();

async function init() {
  const initialData = await fetchData("-1");
  distributeInGrid(initialData);
  drawGrid(initialData);
  updateDepthIndicator();
}

/**
 * Fetch data from an API based on a given ID.
 * Adjust this function to match your real API endpoint.
 */
async function fetchData(id) {
  try {
    const response = await fetch(`http://127.0.0.1:5000/viztree?parent=${id}`);
    const jsonResponse = await response.json();
    return jsonResponse;
  } catch (err) {
    console.error("Error fetching data:", err);
    return [];
  }
}

/**
 * Assign each data point an (x, y) so that they are evenly spaced
 * in a 2D grid (rows & columns).
 */
function distributeInGrid(data) {
  const n = data.length;
  const colCount = Math.ceil(Math.sqrt(n));
  const rowCount = Math.ceil(n / colCount);
  const cellWidth = (width - margin * 2) / colCount;
  const cellHeight = (height - margin * 2) / rowCount;

  data.forEach((d, i) => {
    const row = Math.floor(i / colCount);
    const col = i % colCount;
    d.x = margin + col * cellWidth + cellWidth / 2;
    d.y = margin + row * cellHeight + cellHeight / 2;
  });
}

/**
 * Draw circles and labels at each (x, y) position with transitions.
 * Circle size adjusts automatically based on the number of nodes.
 */
function drawGrid(data) {
  const circles = svg.selectAll("circle").data(data, d => d.id);
  const labels = svg.selectAll("text.label").data(data, d => d.id);

  // Calculate circle size based on node count
  const maxRadius = 80;
  const minRadius = 20;
  const nodeCount = data.length;
  const radius = Math.max(minRadius, Math.min(maxRadius, 300 / Math.sqrt(nodeCount)));

  // Exit old elements
  circles.exit().transition().duration(500).attr("r", 0).remove();
  labels.exit().transition().duration(500).attr("opacity", 0).remove();

  // Enter new circles
  const enterCircles = circles.enter().append("circle")
    .attr("cx", d => d.x)
    .attr("cy", d => d.y)
    .attr("r", 0)
    .style("fill", "#87CEEB")
    .style("stroke", "#000")
    .style("stroke-width", 2);

  // Enter new labels and wrap text inside circles
  const enterLabels = labels.enter().append("text")
    .attr("class", "label")
    .attr("x", d => d.x)
    .attr("y", d => d.y)
    .attr("opacity", 0)
    .style("text-anchor", "middle")
    .style("dominant-baseline", "middle")
    .style("font-size", `${radius / 4}px`)
    .each(function (d) {
      const lines = wrapText(d.explain, Math.floor(radius / 4));
      lines.forEach((line, i) => {
        d3.select(this).append("tspan")
          .attr("x", d.x)
          .attr("dy", i === 0 ? 0 : "1.2em")
          .text(line);
      });
    });

  // Transition circles to final size
  enterCircles.merge(circles).transition().duration(500).attr("r", radius);

  // Transition labels to full opacity
  enterLabels.merge(labels).transition().duration(500).attr("opacity", 1);

  // Click handler to fetch new data
  enterCircles.merge(circles).on("click", async (event, d) => {
    const newData = await fetchData(d.id);
    if (!newData || newData.length === 0) {
      console.log("No data");
      return;
    }
    currentDepth++;
    updateDepthIndicator();

    distributeInGrid(newData);
    svg.selectAll("circle").remove();
    svg.selectAll("text.label").remove();
    drawGrid(newData);
  });
}

/**
 * Helper function to wrap text to fit inside a circle.
 */
function wrapText(text, maxLength) {
  const words = text.split(" ");
  const lines = [];
  let currentLine = "";

  words.forEach(word => {
    if ((currentLine + word).length > maxLength) {
      lines.push(currentLine.trim());
      currentLine = word + " ";
    } else {
      currentLine += word + " ";
    }
  });

  lines.push(currentLine.trim());
  return lines;
}

/**
 * Update the depth indicator on the UI.
 */
function updateDepthIndicator() {
  depthIndicator.textContent = `Depth: ${currentDepth}`;
}
