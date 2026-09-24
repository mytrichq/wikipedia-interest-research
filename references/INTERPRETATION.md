# Interpreting results for product decisions

Read this before writing recommendations, ranking audiences, or filling the report narrative. The user is a founder deciding what to test next, not a statistician. Be direct, quote the tool's numbers, and name the uncertainty.

## Contents

1. From verdict and trust to wording
2. Recommending audiences or topics
3. Limitations to state every time
4. Example answers

## 1. From verdict and trust to wording

| Verdict | Trust High | Trust Medium | Trust Low |
|---|---|---|---|
| `growing` | "Interest is growing (+X%), and the signal is solid." | "Interest seems to be growing (+X%), but <reason>." | "The numbers show +X%, but they cannot be trusted: <reason>." |
| `declining` | "Interest is falling (−X%); this is consistent across months." | "Interest seems to be falling (−X%), with a caveat: <reason>." | "A decline appears, but the data is too weak to rely on: <reason>." |
| `stable` | "Interest is flat (±X%)." | "Roughly flat, with a caveat: <reason>." | "No clear change, and the data is thin." |
| `unclear` | — | "No consistent direction: months disagree." | "No usable signal." |

**Always add the main trust reason in plain words:**

- `edition_effect`: "the whole Polish Wikipedia also fell by 9%, so part of this is not about the topic".
- `one_off_months` / `spike_driven`: "last year was inflated by <event month>, so the drop is partly a return to normal".
- `seasonality_handled`: "the September peak is the school year, not growth".
- `low_volume`: "only ~40 views a month; a few readers change the picture".
- `proxy_article`: "Polish has no article on this; we used a broader article as a stand-in".
- `new_article`: "the article is new, so early growth is mechanical".

## 2. Recommending audiences or topics

- Recommend **what to validate next**, never a final go/no-go. Wikipedia interest is a cheap early signal.
- **Use the ranking, then sanity-check it**:
  - a top rank with Low trust is not a recommendation;
  - a big, stable audience can beat a small, fast-growing one if the user said size matters.
- **Name what drove each rank** (`strongest`): "Polish ranks first mainly on audience size; Czech grows faster but is smaller".
- **Keep the two kinds of zero apart:**
  - *No article* in a language is a content gap. It may be an opportunity (less competition), or a sign of low interest. Suggest validating it with search trends.
  - *Declining everywhere* often means the whole Wikipedia is shrinking (AI answers in search). Compare `relative_yoy_pct` across languages. The one that falls least relative to its edition is holding attention best.
- **Good next steps are concrete and cheap**:
  - search volume in the target country;
  - a landing page test;
  - app-store keyword competition;
  - a survey of existing users;
  - launching seasonal content before the peak month.

## 3. Limitations to state every time

1. Interest in an encyclopedia article ≠ demand or willingness to pay.
2. A language edition ≠ a country. Use `readers_by_country`. If it is marked `MISLEADING WITHOUT CAVEAT`, say the main country's readers are hidden by Wikimedia (a privacy protection list) instead of quoting shares.
3. One article is a proxy for a topic; related articles may behave differently.
4. Wikipedia's total traffic is falling in many languages, so relative figures matter more than absolute ones.
5. Any proxy article, missing article, low volume or one-off event from the output.

## 4. Example answers

**Ukrainian, single language (astronomy, uk):**

> **Інтерес до астрономії в українській Вікіпедії не зростає, а падає: −62% рік до року, довіра висока.**
> - Усі 12 останніх місяців нижчі, ніж рік тому, тож це стійкий спад, а не шум.
> - Щовересня є сезонний пік ≈2.3× (навчальний рік), і це не ріст.
> - Уся українська Вікіпедія втратила 25% переглядів, але й відносно неї тема впала на 42%.
>
> **Обмеження:** інтерес до статті ≠ готовність платити; українську Вікіпедію читають і поза Україною (США 11%).
> **Далі:** перевірити пошукові запити й опитати користувачів; якщо курс запускати, то до вересня.

**English, comparison with a missing article (intermittent fasting, pl vs cs):**

> **Czech interest is falling (−49% year over year, trust High); Polish Wikipedia has no article on intermittent fasting at all.**
> - Czech: 0 of 12 months above last year; about 183 views a month.
> - Polish: no dedicated article. That is a content gap, not zero interest. A broader article ("Głodówka lecznicza") can serve as a labelled proxy if you want a rough signal.
>
> **Next:** check Polish search demand for "post przerywany" before deciding; the missing article may mean less competition.
