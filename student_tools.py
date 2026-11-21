import re
from datetime import date

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "with", "as",
    "is", "are", "be", "by", "at", "from", "this", "that", "you", "your", "we",
    "our", "will", "have", "has", "it", "its", "they", "their", "them", "who",
    "what", "when", "where", "how", "not", "but", "if", "then", "than", "so",
    "can", "could", "should", "would", "may", "might", "must", "do", "does",
    "did", "about", "into", "over", "after", "before", "between", "under",
    "per", "etc", "e.g", "i.e", "also", "such", "using", "use", "used",
    "work", "working", "experience", "team", "role", "job", "candidate",
    "ability", "strong", "good", "knowledge", "skills", "skill", "plus",
    "years", "year", "including", "include", "related", "within", "across",
}


def keywords(text):
    words = re.findall(r"[A-Za-z][A-Za-z+#.\-]{1,}", text.lower())
    return {w.strip(".") for w in words if len(w) > 2 and w not in STOPWORDS}


def resume_match(resume_text, jd_text):
    resume_words = keywords(resume_text)
    jd_words = keywords(jd_text)
    if not jd_words:
        return 0, []
    missing = sorted(jd_words - resume_words)
    score = round(100 * (len(jd_words) - len(missing)) / len(jd_words))
    return score, missing


def make_study_plan(subjects, weak_topics, exam_date, hours_per_day):
    days_left = (exam_date - date.today()).days
    if days_left < 1:
        return None
    rows = []
    order = list(subjects)
    # weak topics get an extra slot every cycle
    boosted = order + [s for s in order if any(w.lower() in s.lower() or s.lower() in w.lower() for w in weak_topics)]
    for day in range(1, days_left + 1):
        subject = boosted[(day - 1) % len(boosted)] if boosted else ""
        weak_hit = subject in order and any(w.lower() in subject.lower() or subject.lower() in w.lower() for w in weak_topics)
        rows.append({
            "Day": day,
            "Subject": subject,
            "Hours": hours_per_day + (1 if weak_hit else 0),
            "Focus": "weak topic - extra hour" if weak_hit else "regular study",
        })
    return rows


def parse_deadlines(text):
    """Pull 'task - date' lines out of AI output into rows."""
    rows = []
    for line in text.splitlines():
        line = line.strip().lstrip("-*0123456789. ")
        if not line or " - " not in line and "–" not in line:
            continue
        parts = re.split(r"\s[-–]\s", line, maxsplit=1)
        if len(parts) == 2:
            rows.append({"Task": parts[0].strip(), "Deadline": parts[1].strip()})
    return rows
