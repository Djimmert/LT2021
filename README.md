## TO DO ##



#### INPUT AND OUTPUT ####
- [Jas] Read questions from CSV
- [Jas] Write answers to CSV: also lists and answer if none

#### QUESTION HANDLING ####
- [Jas] Find entity for location (Falcon)
- [Jas] Find entity for time (Falcon) [Jas]
- Find entity for what_A_is_X_Y (Falcon)
- Find entity for what_which_verb
- Find entity for whatXisY
- Find entity for about
- Find entity for what_is_Xs_Y
- [Jas] Find entity and property for tall
- [Jas] Find entity and property for count
- [Jas] Find entity and property for cost

- [Esther] Detect + answer yes/no question
- Handle questions starting with verb
- For what/which questions   
- [Jas] Return months if asked for months

#### ANSWER RETRIEVAL ####
- [Esther] Choose best answer from candidates


### OTHER ###
- [Jas] Installation instructions


#### PROGRESS AND NOTES ####

When it comes to yes/no questions:
- Detection works well: check if Did/Do/Does/...(etc.) at the start of a question
- Finding entity and property goes well: ENT is from did/do/does (0) to ROOT, property is from root to end (then filter)
- Problems:
-   - 'star' in Did Pamela Anderson star in Borat? is tagged as a noun...
-   - 'Did Leonardo Dicaprio win an Oscar?' works fine, but '...an Oscar for XXX' seems too hard...
-   - Bechdel test: if the value is 'failed', is still counts it as yes in the current system. I will fix this.
