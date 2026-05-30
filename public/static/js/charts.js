(() => {
  // Command Center chart palette
  const PALETTES = {
    default: ["#c6f542", "#8b8cf7", "#67e8f9", "#ff9a55", "#ff5c7a", "#ffd166", "#6be3a6", "#a78bfa"],
    status:  ["#6be3a6", "#ffd166", "#ff5c7a", "#8b8cf7", "#67e8f9"],          // Implemented / Partial / Not / N/A / Not Assessed
    evidence:["#6be3a6", "#ff5c7a", "#ff9a55", "#ffd166", "#8b8cf7", "#67e8f9"], // Available / Missing / Incomplete / Outdated / Needs Review / Accepted
    risk:    ["#ff5c7a", "#ff9a55", "#ffd166", "#c6f542", "#67e8f9", "#8b8cf7", "#a78bfa", "#6be3a6"],
    pipeline:["#8b8cf7", "#67e8f9", "#ffd166", "#ff9a55", "#a78bfa", "#6be3a6"], // Open / In Progress / Pending / Blocked / Risk Accepted / Closed
    cloud:   ["#ff9a55", "#67e8f9", "#a78bfa", "#c6f542", "#8b94aa"],
  };

  function themeColors() {
    const isLight = document.documentElement.getAttribute("data-theme") === "light";
    return {
      text: isLight ? "#0f172a" : "#e8ecf5",
      muted: isLight ? "#5b6478" : "#8b94aa",
      grid: isLight ? "rgba(15,23,42,.06)" : "rgba(255,255,255,.06)",
    };
  }

  function renderChart(canvas) {
    const config = JSON.parse(canvas.dataset.chart);
    const colors = PALETTES[config.palette] || PALETTES.default;
    const t = themeColors();

    Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.color = t.muted;

    const isDoughnut = config.type === "doughnut";

    new Chart(canvas, {
      type: config.type || "bar",
      data: {
        labels: config.labels,
        datasets: [{
          data: config.values,
          backgroundColor: colors,
          borderColor: isDoughnut ? "transparent" : colors,
          borderWidth: 0,
          borderRadius: isDoughnut ? 0 : 8,
          maxBarThickness: 36,
          hoverOffset: isDoughnut ? 6 : 0,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: isDoughnut ? "68%" : undefined,
        plugins: {
          legend: {
            position: "bottom",
            labels: {
              boxWidth: 8, boxHeight: 8, usePointStyle: true, padding: 12,
              color: t.text,
            },
          },
          tooltip: {
            backgroundColor: "rgba(10, 13, 22, 0.92)",
            borderColor: "rgba(255,255,255,0.08)",
            borderWidth: 1,
            padding: 10,
            titleColor: "#fff",
            bodyColor: "#e8ecf5",
            displayColors: false,
          },
        },
        scales: isDoughnut ? {} : {
          x: { ticks: { color: t.muted }, grid: { color: t.grid, drawBorder: false } },
          y: { beginAtZero: true, ticks: { color: t.muted, precision: 0 }, grid: { color: t.grid, drawBorder: false } },
        },
      },
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("canvas[data-chart]").forEach(renderChart);
  });

  // Re-render charts when the theme is toggled
  window.addEventListener("safeguard:theme-change", () => {
    Chart.helpers.each(Chart.instances, (chart) => chart.destroy());
    document.querySelectorAll("canvas[data-chart]").forEach(renderChart);
  });
})();
