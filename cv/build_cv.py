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
               "–": "--", "—": "---", "’": "'", "×": r"\(\times\)",
               "²": r"\squared{}"}
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


def section(title, min_space=None):
    spacing = "[" + min_space + "]" if min_space else ""
    return r"\cvsection" + spacing + "{" + tex(title) + "}"


def entry(title, date, subtitle, body, command="cventry"):
    return "\\" + command + "{" + tex(title) + "}{" + tex(date) + "}{" + tex(subtitle) + "}{" + body + "}"


def compact_entry(title, date, body):
    return r"\compactentry{" + tex(title) + "}{" + tex(date) + "}{" + tex(body) + "}"


def main():
    config = read("_config.yml")
    authors = read("_data/authors.yml")
    data = read("_data/cv.yml")
    publications = [p for p in read("_data/publications.yml") if p.get("in_cv", True)]

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
        highlights = ""
        if p.get("cv_highlights"):
            highlights = r"\begin{itemize}[leftmargin=12pt,label=\textbullet,itemsep=1pt,parsep=0pt,topsep=2pt]"
            highlights += "\n".join(r"\item " + linked_tex(point) for point in p["cv_highlights"])
            highlights += r"\end{itemize}"
        return r"\paper{" + tex(url) + "}{" + tex(title) + "}{" + author_text + "}{" + tex(venue) + "}{" + resource_text + "}{" + highlights + "}"

    lines = [r"{\fontsize{26}{29}\selectfont " + tex(config["name"]) + r"}\par\vspace{5pt}",
             r"{\sffamily " + tex(config["position"]) + r" \enspace\textbar\enspace Rutgers University}\par\vspace{5pt}",
             r"{\small " + link("mailto:" + config["email"], config["email"]) + r"\enspace\textbar\enspace " + link(config["url"], "kowndinya2000.github.io") + r"\enspace\textbar\enspace " + link("https://scholar.google.com/citations?user=" + config["google_scholar"], "Google Scholar") + r"}\par",
             r"{\sffamily\scriptsize Updated " + tex(data["updated"]) + r"}\par",
             section("Introduction"), tex(data["introduction"]),
             section("Education")]
    for school in read("_data/education.yml"):
        subtitle = school["degree"] + ("; GPA: " + school["gpa"] if school.get("gpa") else "")
        body = ("Advisors: " if len(school["advisors"]) > 1 else "Advisor: ") + ", ".join(tex("Prof. " + name(a)) for a in school["advisors"])
        if school.get("detail"):
            body += r"\par {\small " + tex(school["detail"]) + "}"
        lines.append(entry(school["name"], school["dates"], subtitle, body, command="educationentry"))
    lines.append(section("Research experience"))
    for job in read("_data/employment.yml"):
        if job.get("compact"):
            lines.append(compact_entry(job["company"], job["dates"], job["role"] + "; " + job["description"]))
            continue
        body = tex(job.get("description", ""))
        if job.get("highlights"):
            body += r"\begin{itemize}[leftmargin=13pt,itemsep=2pt,parsep=0pt,topsep=3pt]"
            body += "\n".join(r"\item " + linked_tex(point) for point in job["highlights"])
            body += r"\end{itemize}"
        lines.append(entry(job["company"], job["dates"], job["role"] + " · " + job["location"], body))
    lines.append(section("Publications"))
    for heading, first_author in (("First-Author", True), ("Co-Author", False)):
        lines.extend([r"\cvsubsection{" + heading + "}", r"\begin{papers}"])
        lines.extend(paper(p) for p in publications
                     if bool(authors[p["authors"][0]].get("is_me")) == first_author)
        lines.append(r"\end{papers}")
    lines.extend([section("Teaching experience"),
                  r"\begin{description}[leftmargin=78pt,labelwidth=70pt,labelsep=8pt,align=left,font=\normalfont,itemsep=3pt,parsep=0pt,topsep=0pt]"])
    for course in data["teaching"]:
        title = link(course["url"], course["course"]) if course.get("url") else tex(course["course"])
        role = tex(course["role"])
        if course["role"] == "Course Instructor":
            role = r"\textbf{" + role + "}"
        lines.append(r"\item[" + tex(course["dates"]) + "] " + title + ", " + role + ", " + tex(course["name"]))
    lines.extend([r"\end{description}", section("Peer review"),
                  r"\begin{itemize}[leftmargin=13pt,itemsep=2pt,parsep=0pt,topsep=3pt]"])
    for item in data["reviewing"]:
        lines.append(r"\item " + tex(item["venue"] + " (" + item["years"] + ")"))
    lines.extend([r"\end{itemize}", section("Honors & awards")])
    for award in data["awards"]:
        lines.append(r"\textbf{" + tex(award["date"]) + r"}\enspace " + tex(award["title"]) + r". {\small " + tex(award["detail"]) + r"}\par\vspace{4pt}")
    lines.append(section("Skills"))
    for skill in data["skills"]:
        lines.append(r"\textbf{" + tex(skill["label"]) + r":}\enspace " + tex(skill["text"]) + r"\par\vspace{2pt}")
    lines.append(section("Leadership & mentoring"))
    for role in data["leadership"]:
        if role.get("compact"):
            lines.append(compact_entry(role["name"], role["dates"], role["role"] + "; " + role["description"]))
        else:
            lines.append(entry(role["name"], role["dates"], role["role"], tex(role["description"])))
    lines.append(section("Professional service & activities", min_space="60pt"))
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
