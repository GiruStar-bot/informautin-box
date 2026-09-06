const CREDITS = {
  gdelt: {
    name: "GDELT Project",
    url: "https://www.gdeltproject.org/",
    description:
      "Global Database of Events, Language, and Tone — リアルタイムでグローバルイベントを監視・分析するオープンデータプラットフォーム",
  },
  natural: {
    name: "Natural Earth",
    url: "https://www.naturalearthdata.com/",
    description:
      "パブリックドメインの地図データセット — 自然・文化地理データを提供",
  },
  economic: {
    name: "World Bank Open Data",
    url: "https://data.worldbank.org/",
    description: "世界銀行のオープンデータ — 各国の経済・開発指標を提供",
  },
};

export default function DataSourceCredits({ activeLayer }) {
  const credit = CREDITS[activeLayer];

  if (!credit) {
    return (
      <div style={{ padding: "0.5rem", color: "#6a737d" }}>
        データソース情報がありません
      </div>
    );
  }

  return (
    <div
      style={{
        padding: "0.75rem 1rem",
        background: "#f6f8fa",
        border: "1px solid #d1d5da",
        borderRadius: "6px",
        fontSize: "0.875rem",
        lineHeight: 1.5,
      }}
    >
      <strong>データソース:</strong>{" "}
      <a
        href={credit.url}
        target="_blank"
        rel="noopener noreferrer"
        style={{ color: "#0366d6" }}
      >
        {credit.name}
      </a>
      <div style={{ marginTop: "0.25rem", color: "#586069" }}>
        {credit.description}
      </div>
    </div>
  );
}
