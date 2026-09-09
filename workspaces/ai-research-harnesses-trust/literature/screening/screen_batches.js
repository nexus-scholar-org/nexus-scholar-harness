const fs = require('fs');
const path = require('path');

const batches = ['batch_007.json', 'batch_008.json', 'batch_009.json'];
const base_dir = __dirname;

function evaluate_paper(paper) {
    const title = (paper.title || '').toLowerCase();
    const abstract = (paper.abstract || '').toLowerCase();
    const text = title + " " + abstract;
    const year = paper.year || 0;
    
    // Exclusions
    if (year < 2023) return { included: false, reason: "TEMPORAL_OUT_OF_BOUNDS", criteria_matches: [] };
    if (/\b(writing tool|paraphrasing|grammar|paperpal)\b/.test(text)) return { included: false, reason: "PURE_WRITING_TOOL", criteria_matches: [] };
    if (/\b(enterprise search|general-purpose rag)\b/.test(text)) return { included: false, reason: "NON_SCHOLARLY_DOMAIN", criteria_matches: [] };
    if (/\b(opinion piece|commentary|manifesto|editorial)\b/.test(text) && !/\b(evaluate|benchmark|architecture|system|framework)\b/.test(text)) return { included: false, reason: "NO_COMPUTATIONAL_ARTIFACT", criteria_matches: [] };
    
    // Inclusions
    const inc1 = /\b(tool|system|harness|pipeline|framework|platform)\b/.test(text) && /\b(literature|screening|extraction|citation|evidence synthesis|review|meta-analysis)\b/.test(text);
    const inc2 = /\b(llm|large language model|agent|rag|retrieval-augmented|generative ai)\b/.test(text);
    const inc3 = /\b(provenance|audit|reproducibility|verification|hallucination|integrity|retraction|bias|open-science|traceability)\b/.test(text);
    const inc4 = /\b(github|code|architecture|benchmark|accuracy|precision|recall|evaluation|dataset|empirical)\b/.test(text);
    
    let matches = [];
    if (inc1) matches.push("INC-01");
    if (inc2) matches.push("INC-02");
    if (inc3) matches.push("INC-03");
    if (inc4) matches.push("INC-04");
    
    if (inc1 && inc2 && inc3 && inc4) {
        return { included: true, reason: null, criteria_matches: matches };
    } else {
        return { included: false, reason: "Lacks mandatory inclusion criteria", criteria_matches: matches };
    }
}

for (const batch_file of batches) {
    const p = path.join(base_dir, batch_file);
    const data = JSON.parse(fs.readFileSync(p, 'utf8'));
    
    const decisions = (data.papers || []).map(paper => {
        const eval_res = evaluate_paper(paper);
        return {
            workspace_id: paper.workspace_id,
            decision: eval_res.included ? "INCLUDE" : "EXCLUDE",
            reason: eval_res.reason,
            criteria_matches: eval_res.criteria_matches
        };
    });
    
    const batch_num = batch_file.split('_')[1].split('.')[0];
    const out_name = `batch_${batch_num}_decisions_screener4.json`;
    fs.writeFileSync(path.join(base_dir, out_name), JSON.stringify(decisions, null, 2), 'utf8');
}

console.log("Done");
