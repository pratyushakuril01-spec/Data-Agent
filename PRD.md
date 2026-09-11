GAATA Prompt Templates

Ready-to-Use ChatGPT Prompts for Generative AI-Augmented Thematic Analysis

Adapted from Jayawardene, V., & Ewing, M. T. (2025). Generative AI-Augmented Thematic Analysis. International Journal of Market Research, 68(2), 162–193.

How to Use These Templates

These templates implement the GAATA methodology's four core prompts (P1–P4) plus two Step-8 refinement prompts, following the paper's Appendix A prompt-engineering guidelines. Each prompt is a conversational prompt — paste it as a single message, get the response, then continue the conversation with the next prompt in sequence.

Before you start, replace every blue bold placeholder with your own details:

• <research goal> — your specific research question, e.g. "Uncover the pedagogical impacts of technology integration in marketing education"

• <file name> — the data file you upload to ChatGPT (e.g. Abstracts.txt, Transcripts.docx)

• <domain> / <theoretical framework> — your field and any theory you're using (e.g. TPACK, Theory of Planned Behavior) — omit if your analysis is purely inductive

• <A-2> / <A-6> — paste in your own code or theme list where indicated

Recommended workflow (2-tool triangulation, as in the original study):

1. Run P1.1 in ChatGPT (or your primary gen AI tool) to generate the first batch of codes.

2. Run P1.2 repeatedly (same chat) until responses slow or repeat — codes are saturating.

3. Run P1.3 to formally confirm saturation.

4. Human review: remove codes lacking valid excerpts; refine wording.

5. Run P2 in a second gen AI tool to rate/validate the codes (0–10) against your source data.

6. Human review: remove zero-rated codes; examine low-rated codes; finalize the codebook.

7. Run P3 (Tool 1) to synthesize themes from the finalized, rated codes.

8. Human review: confirm themes represent their underlying codes.

9. Run P4 (Tool 2) to rate the themes for relevance.

10. Human review: use the Theme Consolidation prompt to merge overlapping themes, and the Improve Theme Wording prompt to polish final names/descriptions.

Tip: keep P1.1/P1.2/P2/P3/P4 running in the same chat thread per tool so each prompt has the prior context ("conversational prompting"). When switching tools, paste the relevant artefact (A-2, A-4, A-6) directly into the new prompt, since the second tool won't have the first tool's chat history.

P1.1 — Generate Initial Codes

Gen AI Tool 1  ·  Step 1  ·  First message in a new chat

### Task:

As an expert in thematic analysis (Braun & Clarke, 2006), develop thematic codes from the text in the input data file provided below. Use the research goal and the data analysis instructions specified below in developing thematic codes. Display the response according to the given output specification and example output.

 

### Research Goal: <research goal>

 

### Input Data:

  Source data File: <file name and format, e.g. Abstracts.txt>

 

### Data Analysis Instructions:

1. ## Code Development:

   Thoroughly examine the input data and generate codes that directly relate to the research goal above. Use the following guidelines:

   I. Codes serve as labels/tags that assign meaningful units to the data, facilitating the identification of patterns and themes (Braun & Clarke, 2019).

   II. Coding involves systematically categorizing segments of data (phrases, sentences, paragraphs) based on their relevance to the research goal, enabling the researcher to uncover underlying themes (Boyatzis, 1998).

   III. <special experience / domain context from researchers, if any>

   Generate the maximum number of unique codes.

2. ## Code Specificity:

   Use direct, explicit language from the input data as the foundation for each code.

   Avoid drawing inferences beyond the explicit content of the data file.

   Avoid creating overarching themes at this stage.

3. ## Code and Excerpt Linkage:

   Substantiate each code with precise excerpts (phrases, sentences, or paragraphs) that illustrate the code's meaning.

4. ## Formatting:

   Code Numbering: assign a unique Arabic numeral to each code.

   Excerpts: present supporting excerpts as bullet points below their corresponding code.

5. ## Key Considerations:

   Emphasis on explicit content; ensure each code is accompanied by clear evidence from the source text.

 

### Output specification:

A clearly structured list of codes and their associated precise excerpts that demonstrate each code.

 

### Example Output:

1: Enhanced Student Engagement

   "Students showed increased engagement during lessons that incorporated interactive technology tools."

2: Technological Challenges

   "Some students faced difficulties in accessing the necessary technology for completing assignments."

 

### References:

Braun, V., & Clarke, V. (2006). Using thematic analysis in psychology. Qualitative Research in Psychology, 3(2), 77-101.

Braun, V., & Clarke, V. (2019). Reflecting on reflexive thematic analysis. Qualitative Research in Sport, Exercise and Health, 11(4), 589-597.

Boyatzis, R. E. (1998). Transforming qualitative information: Thematic analysis and code development. Sage.

P1.2 — Generate Additional Codes

Gen AI Tool 1  ·  Step 1 (continued)  ·  Run repeatedly in the same chat

### Task:

As an expert in thematic analysis (Braun & Clarke, 2006), conduct a follow-up code-based thematic analysis from the text in the input data file provided below. Use the research goal and data analysis instructions specified below. Display the response according to the given output specification and example output. Do NOT duplicate existing codes you have developed so far.

 

### Research Goal: <research goal>

 

### Input Data:

  Source data File: <same file as P1.1>

 

### Data Analysis Instructions:

1. ## Code Development: (same guidelines as P1.1)

   Generate the maximum number of unique NEW codes not already produced.

2. ## Code Specificity: (same as P1.1) — also avoid duplicating any codes developed so far.

3. ## Code and Excerpt Linkage: (same as P1.1)

4. ## Formatting:

   Code Numbering: continue numbering from the last code number generated above.

   Excerpts: present supporting excerpts as bullet points below their corresponding code.

5. ## Key Considerations: (same as P1.1)

 

### Output specification / Example Output / References: same as P1.1

 

P1.3 — Check for Saturation

Gen AI Tool 1  ·  Step 1 (final check)  ·  Same chat as P1.1/P1.2

### Task:

If you have reached a saturation point where you cannot generate any more new codes, then print:

  "Saturation point reached. I cannot generate any more new codes."

Else print:

  "I can generate more codes" and give an approximate time you need to generate them.

In the original study, saturation was signaled by 10–15 minutes of inactivity from the tool while running P1.2 repeatedly. Once codes stop growing, run P1.3 to confirm, then move to human review (Step 2) before Step 3 (P2).

P2 — Rate and Validate Codes

Gen AI Tool 2  ·  Step 3  ·  New chat; paste your human-verified code list as A-2

### Task:

As an expert in qualitative data analysis, rate the codes in A-2 provided below by analysing them against the input data file provided below. Use the research goal and the Data Analysis Instructions specified below in rating the codes. Display the response according to the given output specification and example output.

 

### Research Goal: <research goal>

 

### Input Data:

1. A-2: provided at the bottom of the prompt

   Format of A-2: each code is assigned a unique Arabic numeral, with supporting excerpts as bullet points below the code.

2. Source Data File: <file name> (to verify the relevance of each code and its supporting excerpts)

 

### Data Analysis Instructions: (perform for each code in A-2)

1. Extract Code: access A-2 and extract a code with its supporting excerpts.

2. Analyse code: recognize the meaning of the data pattern using the excerpts (Boyatzis, 1998).

3. Code validation: independently search the Source Data File for excerpts matching that meaning, referring to Braun & Clarke (2006).

4. Evaluate Meaning: if ≥1 matching excerpt is found, proceed to Step 5 (Rate); if none, proceed to Step 6 (Not Applicable).

5. Rate the code: assign a rating 0–10 (0 = irrelevant to Research Goal, 10 = most relevant).

6. Code Not Applicable: if no excerpt clearly matches, assign the rating as "NA".

7. Populate Table-1 with the code's details, then move to the next code.

8. Key Consideration: strictly follow steps 1–7 for all codes; maintain the original order of codes in A-2.

 

### Output specification:

Table-1 with columns: Code Number | Code | Rate

 

### Example Output Format:

Code Number | Code | Rate

1 | Enhanced Student Engagement | 8

2 | Improved Understanding of Concepts | 9

3 | Faculty decisions on recruitments | NA

 

### References:

Braun, V., & Clarke, V. (2019). Reflecting on reflexive thematic analysis. Qualitative Research in Sport, Exercise and Health, 11(4), 589-597.

Boyatzis, R. E. (1998). Transforming qualitative information: Thematic analysis and code development. Sage.

Stevens, S. S. (1946). On the theory of scales of measurement. Science, 103(2684), 677-680.

 

### A-2: <paste the list of codes with their excerpts here>

P3 — Generate Themes

Gen AI Tool 1  ·  Step 5  ·  New chat; use your finalized, rated codes (A-4) as input

### Task:

As an expert in thematic analysis (Braun & Clarke, 2006, 2019), develop a set of prominent themes from the codes in the input data file provided below. Use the research goal and the data analysis instructions specified below for developing themes. Display the response according to the given output specification and example output.

 

### Research Goal: <research goal>

 

### Input Data:

  Source Data File: <validated/rated codes file, e.g. A-4> — format: a table with three columns: Code Number, Code, Rate

 

### Data Analysis Instructions:

1. ## Theme Development:

   Content Analysis: analyze the codes, paying close attention to their relevance ratings.

   Theoretical Integration (for deductive TA only): evaluate how each code aligns with <your theoretical framework / classification / domain expertise, if applicable> (Sinclair-Maragh & Simpson, 2021).

   Theme generation: synthesize the codes into broader, meaningful patterns that address the Research Goal (and the theoretical framework, if specified). Refer to Braun & Clarke (2006, 2019) for guidance.

   Code Prioritization: prioritize codes with higher ratings.

2. ## Theme Specificity:

   Internal Consistency: ensure each theme is internally consistent and codes within it are cohesive (Patton, 2023).

   Distinctiveness: ensure each theme is distinct from other themes, avoiding redundancy.

3. ## Theme and Codes Linkage:

   Code Justification: for each theme, provide supporting codes (by number) from the Source Data File.

4. ## Formatting:

   Theme Numbering: assign a unique Arabic numeral to each theme.

   Codes: list supporting codes beneath each theme, referencing code numbers and ratings.

5. ## Key Considerations:

   Code Coverage: ensure all codes are included in at least one theme; each theme should be built from multiple codes.

 

### Output specification:

A well-structured list of themes and their associated codes.

 

### Example Output Format:

Theme 1: Improving student satisfaction (Dimension: Technological Pedagogical Knowledge - TPK)

  Code 7: "Increased student satisfaction during lessons using interactive tools." (Rating 9)

  Code 18: "Higher participation rates in classes using technology." (Rating 10)

 

### References:

Braun, V., & Clarke, V. (2006). Using thematic analysis in psychology. Qualitative Research in Psychology, 3(2), 77-101.

Braun, V., & Clarke, V. (2019). Reflecting on reflexive thematic analysis. Qualitative Research in Sport, Exercise and Health, 11(4), 589-597.

Patton, M. Q. (2023). Qualitative research & evaluation methods: Integrating theory and practice. Sage.

Sinclair-Maragh, G., & Simpson, S. B. (2021). Heritage tourism and ethnic identity: A deductive thematic analysis of Jamaican Maroons. Journal of Tourism, Heritage & Services Marketing, 7(1), 64-75.

P4 — Rate and Validate Themes

Gen AI Tool 2  ·  Step 7  ·  New chat; paste your preliminary theme list as A-6

### Task:

As an expert in qualitative data analysis, rate the themes in A-6 provided below by analysing them against the input data file provided below. Use the research goal and the Data Analysis Instructions specified below in rating the themes. Display the response according to the given output specification and example output.

 

### Research Goal: <research goal>

 

### Input Data:

1. A-6: provided at the bottom of the prompt — each theme numbered, with supporting codes as bullets below it.

2. Source Data File: <validated/rated codes file, e.g. A-4> — table with columns: Code Number, Code, Rating

 

### Data Analysis Instructions: (perform for each theme in A-6)

1. Extract theme: access A-6 and extract a theme with its supporting codes.

2. Analyse theme: recognize the meaning of the theme by synthesising its codes into a broader pattern (Braun & Clarke, 2019) aligned with the Research Goal <and relevant theoretical dimension, if applicable>.

3. Theme validation: independently search the Source Data File for supporting codes that cohesively match the meaning identified in step 2 (Patton, 2023).

4. Evaluate Meaning: if ≥1 code clearly matches, proceed to Step 5 (Rate); if none, proceed to Step 6 (Not Applicable).

5. Rate the Theme: assign a rating 0–10 (0 = irrelevant to Research Goal, 10 = most relevant).

6. Theme Not Applicable: if fewer than two codes clearly match, assign the Rating as "NA".

7. Populate Table-1 with the theme's details, then move to the next theme.

8. Key Consideration: strictly follow steps 1–7 for all themes; maintain the original order of themes in A-6.

 

### Output specification:

Table-1 with columns: Theme Number | Theme | Rating

 

### Example Output Format:

Theme Number | Theme | Rating

1 | Enhanced Student Engagement | 9

2 | Improved Understanding of Concepts | 8

3 | Business Faculty Growth perspectives | NA

 

### References:

Braun, V., & Clarke, V. (2019). Reflecting on reflexive thematic analysis. Qualitative Research in Sport, Exercise and Health, 11(4), 589-597.

Boyatzis, R. E. (1998). Transforming qualitative information: Thematic analysis and code development. Sage.

Stevens, S. S. (1946). On the theory of scales of measurement. Science, 103(2684), 677-680.

 

### A-6: <paste the list of themes with their supporting codes here>

Step 8a — Improve Theme Wording

Either tool  ·  Final human-AI refinement of individual themes

Task:

Provide a more comprehensive and appealing name and description for Theme-xx (provided below) by aligning it with the research question.

 

Research Goal: <research goal>

 

Instructions:

1. Analyze Theme-xx and its supporting codes by comparing with the research goal and recognize the pattern of its broader meaning.

2. Use terminology applicable to <your domain> and enrich the theme definition and description.

3. The final presentation of the theme should have the same format/structure as the given Theme-xx.

4. Do not deviate from the terminology and context in the underlying codes when developing a name and description.

5. Provide justifications for each improvement made above.

 

Theme-xx: <paste the original theme name, description, and underlying codes here>

Step 8b — Check for Overlapping Themes

Either tool  ·  Final human-AI consolidation of theme pairs

Task:

Analyze two themes based on the same research goal and check if they are overlapping themes.

 

Research Goal: <research goal>

 

Instructions:

1. Analyze Theme-A and its supporting codes against the research goal; recognize the pattern of its broader meaning.

2. Analyze Theme-B and its supporting codes against the research goal; recognize the pattern of its broader meaning.

3. If the two themes have overlapping patterns of meaning, consolidate them into a more comprehensive theme and justify the consolidation.

4. If the two themes have distinct data patterns, do not consolidate — instead print "Cannot be consolidated" and provide justification.

 

Theme-A: <paste theme with supporting codes>

Theme-B: <paste theme with supporting codes>

Reference: Prompt Engineering Guidelines

The 9 best-practice principles these templates are built on (Appendix A)

1. Specificity and detail — clearly articulate the task, context, format, and style.

2. Incorporating context — provide relevant background so the AI understands nuanced inquiries.

3. Structured instructions — use markers such as ### to organize the prompt.

4. Leveraging examples — show the desired output format with an example.

5. Clarity and precision — avoid ambiguous language.

6. Using reference texts — cite the qualitative-research literature underpinning each instruction.

7. Iterative refinement — adjust the prompt based on the AI's previous outputs.

8. Roleplay — assign the AI a role ("As an expert in thematic analysis...") to prime context.

9. Conversational prompting — break the task into a sequence of prompts run step by step, rather than one giant instruction.

Source: Jayawardene, V., & Ewing, M. T. (2025). Generative AI-Augmented Thematic Analysis. International Journal of Market Research, 68(2), 162–193. https://doi.org/10.1177/14707853251405043