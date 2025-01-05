// 1️⃣ Treemap 레이아웃 초기화 (기본 설정)
function initializeTreemap(data) {
  // 기본 크기 및 좌표 설정
  var width = 100, // % 기준 크기
    height = 100,

    // x, y 축 스케일 설정
    x = d3.scaleLinear().domain([0, width]).range([0, width]),
    y = d3.scaleLinear().domain([0, height]).range([0, height]),

    // 색상 스케일 설정 (d3.schemeDark2 사용)
    color = d3.scaleOrdinal()
      .range(d3.schemeDark2.map(function(c) {
        c = d3.rgb(c);
        return c;
      })),

    // Treemap 레이아웃 정의
    treemap = d3.treemap()
      .size([width, height])
      .paddingInner(0)
      .round(false),

    // 데이터 구조를 계층 구조로 변환
    nodes = d3.hierarchy(data)
      .sum(function(d) { return d.value ? 1 : 0; });

  // Treemap 레이아웃 적용
  treemap(nodes);

  // 2️⃣ HTML 요소 생성 및 데이터 바인딩
  var chart = d3.select("#chart");
  var cells = chart
    .selectAll(".node")
    .data(nodes.descendants()) // 노드 데이터 바인딩
    .enter()
    .append("div")
    .attr("class", function(d) { return "node level-" + d.depth; }) // 노드 깊이에 따른 클래스 설정
    .attr("title", function(d) { return d.data.name ? d.data.name : "null"; });

  // 3️⃣ 스타일 설정 및 Zoom 이벤트 추가
  cells
    .style("left", function(d) { return x(d.x0) + "%"; })
    .style("top", function(d) { return y(d.y0) + "%"; })
    .style("width", function(d) { return x(d.x1) - x(d.x0) + "%"; })
    .style("height", function(d) { return y(d.y1) - y(d.y0) + "%"; })
    .style("background-color", function(d) {
      while (d.depth > 2) d = d.parent;
      return color(d.data.name);
    })
    .on("click", zoom) // 클릭 시 Zoom 함수 호출
    .append("p")
    .attr("class", "label")
    .text(function(d) { return d.data.name ? d.data.name : "---"; });

  // 클릭된 노드 이후 3단계 깊이 노드 숨기기 (초기화)
  cells
    .filter(function(d) { return d.depth >= 3; })
    .classed("hide", true);

    // 부모 노드로 이동 버튼
  var parent = d3.select(".up")
    .datum(nodes)
    .on("click", zoom);

// 툴팁 요소 생성
var tooltip = d3.select("body")
  .append("div")
  .attr("class", "tooltip")
  .style("position", "absolute")
  .style("visibility", "hidden")
  .style("background-color", "#fff")
  .style("border", "1px solid #ccc")
  .style("padding", "5px")
  .style("border-radius", "5px")
  .style("box-shadow", "0px 0px 10px rgba(0,0,0,0.1)")
  .style("z-index", "1000");


  // 노드 hover 이벤트 추가
  cells
  .on("mouseover", function(d) {
    console.log(d);
    console.log(d.x0);


    if (d.data.type === "doc") {
      tooltip
        .style("visibility", "visible")
        .style("left", function(_) { return (x(d.x0) + x(d.x1))/2 + "%"; })
        .style("top", function(_) { return (y(d.y0)+y(d.y1))/2 + "%"; })
        .html(`<a href="/paper?arg=${d.data.link}" target="_blank">논문 바로가기</a>`);
    }
  })
  .on("mousemove", function(d) {
    tooltip
    .style("left", function(_) { return (x(d.x0) + x(d.x1))/2 + "%"; })
    .style("top", function(_) { return (y(d.y0)+y(d.y1))/2 + "%"; })
  })
  .on("mouseout", function() {
    tooltip.style("visibility", "hidden");
  });


  // 4️⃣ Zoom 함수 정의 (줌 기능 구현)
  function zoom(d) {
    console.log('clicked: ' + d.data.name + ', depth: ' + d.depth);

    let currentDepth = d.depth;
    parent.datum(d.parent || nodes);

    // 도메인 업데이트
    x.domain([d.x0, d.x1]);
    y.domain([d.y0, d.y1]);

    // 트랜지션 효과 적용
    var t = d3.transition()
      .duration(800)
      .ease(d3.easeCubicOut);

    // 스타일 업데이트
    cells
      .transition(t)
      .style("left", function(d) { return x(d.x0) + "%"; })
      .style("top", function(d) { return y(d.y0) + "%"; })
      .style("width", function(d) { return x(d.x1) - x(d.x0) + "%"; })
      .style("height", function(d) { return y(d.y1) - y(d.y0) + "%"; });

    // 현재 노드 깊이보다 깊은 노드 숨기기
    cells
      .filter(function(d) { return d.ancestors(); })
      .classed("hide", function(d) { return d.children ? true : false });

    // 클릭된 노드 이후의 깊이 노드 표시
    cells
      .filter(function(d) { return d.depth > currentDepth; })
      .classed("hide", false);

    // 클릭된 노드 이후 3단계 깊이 노드 숨기기
    cells
      .filter(function(d) { return d.depth >= currentDepth + 3; })
      .classed("hide", true);
  }
}

// 5️⃣ 트리 데이터 동적 생성 함수
function buildTree(data, parentId) {
  const tree = [];
  data.forEach(item => {
    if (item.parent === parentId) {
      const children = buildTree(data, item.id); // 재귀적으로 하위 노드 찾기
      const node = { name: item.explain, value: item.explain, type: item.type, link: item.link ?  item.link : "https://arxiv.org/pdf/1706.03762" };
      if (children.length > 0) {
        node.children = children; // 하위 노드 연결
      }
      tree.push(node);
    }
  });
  return tree;
}

// 6️⃣ 외부 데이터 불러오기 및 Treemap 생성
fetch("viztree")
  .then(response => response.json())
  .then((data) => {
    const outputData = {
      name: "Portfolio",
      children: buildTree(data, "-1") // 최상위 노드 설정
    };
    console.log(outputData);
    initializeTreemap(outputData); // Treemap 초기화 함수 호출
  });
