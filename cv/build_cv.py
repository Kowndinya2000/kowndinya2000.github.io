#!/usr/bin/env python3
"""Generate the CV from the website data and compile its LaTeX source."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
CV = ROOT / "cv"


def read(name):
    return yaml.safe_load((ROOT / name).read_text())


def tex(value):
    escapes = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
               "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
               "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
               "–": "--", "—": "---", "’": "'", "×": r"\(\times\)"}
    return "".join(escapes.get(c, c) for c in str(value))


def link(url, label):
    return r"\href{" + tex(url) + "}{" + tex(label) + "}"


def linked_tex(value):
    """Render inline Markdown links as underlined LaTeX links, escaping other text."""
    parts = []
    end = 0
    for match in re.finditer(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", value):
        parts.append(tex(value[end:match.start()]))
        label, url = match.groups()
        parts.append(r"\href{" + tex(url) + r"}{\underline{" + tex(label) + "}}")
        end = match.end()
    parts.append(tex(value[end:]))
    return "".join(parts)


def section(title):
    return r"\cvsection{" + tex(title) + "}"


def entry(title, date, subtitle, body, command="cventry"):
    return "\\" + command + "{" + tex(title) + "}{" + tex(date) + "}{" + tex(subtitle) + "}{" + body + "}"


def main():
    config = read("_config.yml")
    authors = read("_data/authors.yml")
    data = read("_data/cv.yml")
    publications = read("_data/publications.yml")

    def name(key):
        author = authors[key]
        return " ".join(author[p] for p in ("first_name", "middle_name", "last_name") if author.get(p))

    def paper(p):
        url = p.get("pub_link") or p.get("pdf") or p["url"]
        if not url.startswith("http"):
            url = config["url"] + "/" + url
        resources = [("Paper", url)]
        for key, label in (("project_page", "Project"), ("code", "Code"), ("data", "Data")):
            if p.get(key) and p[key] != url:
                resources.append((label, p[key]))
        resource_text = r"\enspace ".join(r"\resource{" + tex(target) + "}{" + label + "}" for label, target in resources)
        title = p["title"]
        if p["status"] == "under-review" and p.get("prefix_title", True):
            title = p["short_title"] + ": " + title
        author_text = ", ".join(r"\textbf{" + tex(name(a)) + "}" if authors[a].get("is_me") else tex(name(a)) for a in p["authors"])
        venue = p["venue"]
        if p["status"] == "under-review":
            venue = "Manuscript, " + str(p["year"]) + ". " + venue + "."
        return r"\paper{" + tex(url) + "}{" + tex(title) + "}{" + author_text + "}{" + tex(venue) + "}{" + resource_text + "}"

    lines = [r"{\fontsize{26}{29}\selectfont " + tex(config["name"]) + r"}\par\vspace{5pt}",
             r"{\sffamily " + tex(config["position"]) + r" \enspace\textbar\enspace Rutgers University}\par\vspace{5pt}",
             r"{\small " + link("mailto:" + config["email"], config["email"]) + r"\enspace\textbar\enspace " + link(config["url"], "kowndinya2000.github.io") + r"\enspace\textbar\enspace " + link("https://scholar.google.com/citations?user=" + config["google_scholar"], "Google Scholar") + r"}\par",
             r"{\sffamily\scriptsize Updated " + tex(data["updated"]) + r"}\par",
             section("Research interests"), tex(data["research_interests"]),
             section("Education")]
    for school in read("_data/education.yml"):
        subtitle = school["degree"] + ("; GPA: " + school["gpa"] if school.get("gpa") else "")
        body = ("Advisors: " if len(school["advisors"]) > 1 else "Advisor: ") + ", ".join(tex("Prof. " + name(a)) for a in school["advisors"])
        if school.get("detail"):
            body += r"\par {\small " + tex(school["detail"]) + "}"
        lines.append(entry(school["name"], school["dates"], subtitle, body, command="educationentry"))
    lines.extend([section("Manuscripts under review"), r"\begin{papers}"])
    lines.extend(paper(p) for p in publications if p["status"] == "under-review")
    lines.extend([r"\end{papers}", section("Ongoing research projects")])
    for project in read("_data/ongoing_research.yml"):
        lines.append(r"\needspace{85pt}\textbf{" + tex(project["title"]) + r"}\hfill{\small Ongoing}\par")
        lines.append(r"\begin{itemize}[leftmargin=13pt,itemsep=2pt,parsep=0pt,topsep=3pt]")
        lines.extend(r"\item " + tex(point) for point in project["cv_points"])
        lines.append(r"\end{itemize}\par\addvspace{4pt}")
    lines.append(section("Research experience"))
    for job in read("_data/employment.yml"):
        body = tex(job.get("description", ""))
        if job.get("highlights"):
            body += r"\begin{itemize}[leftmargin=13pt,itemsep=2pt,parsep=0pt,topsep=3pt]"
            body += "\n".join(r"\item " + linked_tex(point) for point in job["highlights"])
            body += r"\end{itemize}"
        lines.append(entry(job["company"], job["dates"], job["role"] + " · " + job["location"], body))
    lines.append(section("Teaching"))
    for course in data["teaching"]:
        lines.append(r"\textbf{" + tex(course["role"] + ", " + course["name"]) + r"}\hfill{\small " + tex(course["dates"]) + r"}\par " + link(course["url"], course["course"]) + r"\enspace {\small " + tex(course["level"] + " course") + r"}\par")
    lines.extend([section("Peer-reviewed publications"), r"\begin{papers}"])
    lines.extend(paper(p) for p in publications if p["status"] == "published")
    lines.extend([r"\end{papers}", section("Honors & awards")])
    for award in data["awards"]:
        lines.append(r"\textbf{" + tex(award["date"]) + r"}\enspace " + tex(award["title"]) + r". {\small " + tex(award["detail"]) + r"}\par\vspace{4pt}")
    lines.append(section("Leadership & mentoring"))
    for role in data["leadership"]:
        lines.append(entry(role["name"], role["dates"], role["role"], tex(role["description"])))
    lines.append(section("Technical skills"))
    for skill in data["skills"]:
        lines.append(r"\textbf{" + tex(skill["label"]) + ":} " + tex(skill["text"]) + r"\par")
    lines.append(section("Professional service & activities"))
    reviewer_text = "; ".join(item["venue"] + " (" + item["years"] + ")" for item in data["reviewing"]) + "."
    lines.append(r"\textbf{Reviewer:} " + tex(reviewer_text) + r"\par\vspace{4pt}")
    for item in data["service"]:
        lines.append(r"\textbf{" + tex(item["date"]) + r"}\enspace " + tex(item["description"]) + r"\par\vspace{3pt}")
    (CV / "content.tex").write_text("% Generated by build_cv.py from the website's YAML data.\n" + "\n".join(lines) + "\n")
    with tempfile.TemporaryDirectory(prefix="kowndinya-cv-") as folder:
        out = Path(folder)
        for _ in range(2):
            result = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "-output-directory=" + folder, "kowndinya-cv.tex"], cwd=CV, capture_output=True, text=True)
            if result.returncode:
                raise SystemExit(result.stdout + result.stderr)
        log = (out / "kowndinya-cv.log").read_text()
        for line in log.splitlines():
            if "Overfull" in line or "Output written" in line:
                print(line)
        for filename in ("Kowndinya_Boyalakuntla_CV.pdf", "Kowndinya_Resume.pdf"):
            destination = ROOT / "pdfs" / filename
            shutil.copy2(out / "kowndinya-cv.pdf", destination)
            print(destination)


if __name__ == "__main__":
    main()
