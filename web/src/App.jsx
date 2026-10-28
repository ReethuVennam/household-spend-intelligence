import React, { useEffect, useState } from "react";
import data from "./data.json";
import Header from "./components/Header.jsx";
import Overview from "./components/Overview.jsx";
import Spend from "./components/Spend.jsx";
import Budgets from "./components/Budgets.jsx";
import Recurring from "./components/Recurring.jsx";
import Exceptions from "./components/Exceptions.jsx";
import Explorer from "./components/Explorer.jsx";
import Reports from "./components/Reports.jsx";

const SECTIONS = ["overview", "spend", "budgets", "recurring", "exceptions", "explorer", "reports"];

export default function App() {
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem("hsi-theme") || "light";
    } catch {
      return "light";
    }
  });
  const [active, setActive] = useState("overview");

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem("hsi-theme", theme);
    } catch {
      /* ignore */
    }
  }, [theme]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible) setActive(visible.target.id);
      },
      { rootMargin: "-15% 0px -55% 0px", threshold: [0.1, 0.3, 0.6] }
    );
    SECTIONS.forEach((id) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, []);

  const toggleTheme = () => setTheme((t) => (t === "dark" ? "light" : "dark"));
  const onNav = (id) => setActive(id);

  return (
    <div>
      <Header
        manifest={data.manifest}
        validation={data.validation}
        active={active}
        onToggleTheme={toggleTheme}
        onNav={onNav}
      />
      <div className="wrap">
        <Overview manifest={data.manifest} validation={data.validation} evaluation={data.evaluation} />
        <Spend data={data} evaluation={data.evaluation} />
        <Budgets budget={data.budget} evaluation={data.evaluation} />
        <Recurring recurring={data.recurring} evaluation={data.evaluation} />
        <Exceptions anomalies={data.anomalies} evaluation={data.evaluation} />
        <Explorer explorer={data.explorer} />
        <Reports reports={data.reports} manifest={data.manifest} seed={data.manifest.seed} />
      </div>
    </div>
  );
}
