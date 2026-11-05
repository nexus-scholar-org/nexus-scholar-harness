import type { Locale } from "@/i18n";
import type { DecisionRole } from "@/components/ui/base";

/**
 * The state cards of spec 08: for each typed code the screens can hit, what
 * happened, what it affects and one next step. The code itself is always shown
 * verbatim beside the copy so a supervisor can find it in the journal; an
 * unknown code renders as itself (`stateCopy` falls back, never guesses).
 *
 * `conflict` is a per-event result, not a refusal (contract §3.4); it has a
 * card because the screens must show it, and its role is `unclear`.
 */

export type StateAction = "prepare" | "triage" | "publish" | "home" | "retry" | "reload" | "terminal" | "none";

interface StateEntry {
  role: DecisionRole;
  action: StateAction;
  copy: Record<Locale, { title: string; body: string; affects: string; action: string }>;
}

const T = (title: string, body: string, affects: string, action: string) => ({ title, body, affects, action });

export const STATES: Record<string, StateEntry> = {
  STALE_BINDING: {
    role: "blocked",
    action: "prepare",
    copy: {
      en: T("Protocol changed", "The batches no longer match the protocol. Existing decisions are kept; new ones are disabled until you prepare again.", "Triage and publish", "Prepare again"),
      fr: T("Protocole modifié", "Les lots ne correspondent plus au protocole. Les décisions existantes sont conservées ; les nouvelles sont désactivées jusqu'à une nouvelle préparation.", "Tri et publication", "Préparer à nouveau"),
      ar: T("تغيّر البروتوكول", "لم تعد الدفعات مطابقة للبروتوكول. تُحفظ القرارات الموجودة، وتُعطَّل الجديدة حتى تعيد التحضير.", "المراجعة والنشر", "إعادة التحضير"),
    },
  },
  SNAPSHOT_NOT_ACCEPTED: {
    role: "blocked",
    action: "terminal",
    copy: {
      en: T("No accepted corpus", "Batches can be prepared only from an accepted corpus snapshot. Accept it from the terminal.", "Batch preparation only", "nexus-scholar accept-corpus"),
      fr: T("Aucun corpus accepté", "Les lots ne peuvent être préparés qu'à partir d'un instantané de corpus accepté. Acceptez-le depuis le terminal.", "Préparation des lots uniquement", "nexus-scholar accept-corpus"),
      ar: T("لا توجد مجموعة مقبولة", "لا تُحضَّر الدفعات إلا من لقطة مجموعة مقبولة. اقبلها من الطرفية.", "تحضير الدفعات فقط", "nexus-scholar accept-corpus"),
    },
  },
  NOT_PREPARED: {
    role: "exclude",
    action: "prepare",
    copy: {
      en: T("No batches yet", "Prepare the screening batches to start.", "Everything in screening", "Prepare batches"),
      fr: T("Pas encore de lots", "Préparez les lots de sélection pour commencer.", "Toute la sélection", "Préparer les lots"),
      ar: T("لا توجد دفعات بعد", "حضّر دفعات الفرز للبدء.", "كل مراحل الفرز", "تحضير الدفعات"),
    },
  },
  ENGINE_UNREACHABLE: {
    role: "blocked",
    action: "retry",
    copy: {
      en: T("Engine unreachable", "The screening engine on this computer did not answer. Nothing was recorded by this attempt.", "Every read and decision", "Try again"),
      fr: T("Moteur injoignable", "Le moteur de sélection de cet ordinateur n'a pas répondu. Rien n'a été enregistré par cette tentative.", "Toutes les lectures et décisions", "Réessayer"),
      ar: T("تعذّر الوصول إلى المحرك", "لم يستجب محرك الفرز على هذا الحاسوب. لم يُسجَّل شيء في هذه المحاولة.", "كل القراءات والقرارات", "إعادة المحاولة"),
    },
  },
  conflict: {
    role: "unclear",
    action: "triage",
    copy: {
      en: T("Decided differently on two devices", "Keep one decision; nothing is resolved automatically.", "Publishing", "Open the record"),
      fr: T("Décisions différentes sur deux appareils", "Gardez une décision ; rien n'est résolu automatiquement.", "Publication", "Ouvrir la notice"),
      ar: T("قراران مختلفان على جهازين", "أبقِ على قرار واحد؛ لا يُحسم شيء تلقائيًا.", "النشر", "فتح السجل"),
    },
  },
  PROJECTION_STALE: {
    role: "blocked",
    action: "triage",
    copy: {
      en: T("A decisions file is out of date", "A batch file could not be rewritten after a decision, so it no longer matches the decision log. Re-submit the last decision in that batch.", "Publishing", "Open triage"),
      fr: T("Un fichier de décisions est périmé", "Un fichier de lot n'a pas pu être réécrit après une décision ; il ne correspond plus au journal des décisions. Soumettez à nouveau la dernière décision de ce lot.", "Publication", "Ouvrir le tri"),
      ar: T("ملف قرارات قديم", "تعذّرت إعادة كتابة ملف دفعة بعد قرار، فلم يعد مطابقًا لسجل القرارات. أعد إرسال آخر قرار في تلك الدفعة.", "النشر", "فتح المراجعة"),
    },
  },
  APPROVAL_MISSING: {
    role: "unclear",
    action: "publish",
    copy: {
      en: T("Not approved", "Each batch must be approved with the code shown in the terminal before it can be published.", "Publishing", "Review and approve"),
      fr: T("Non approuvé", "Chaque lot doit être approuvé avec le code affiché dans le terminal avant publication.", "Publication", "Vérifier et approuver"),
      ar: T("غير معتمد", "يجب اعتماد كل دفعة بالرمز المعروض في الطرفية قبل نشرها.", "النشر", "المراجعة والاعتماد"),
    },
  },
  COVERAGE_INCOMPLETE: {
    role: "unclear",
    action: "triage",
    copy: {
      en: T("Records still undecided", "Every record in a batch needs a decision before the batch can be collected.", "Publishing", "Open triage"),
      fr: T("Notices encore non décidées", "Chaque notice d'un lot doit être décidée avant que le lot puisse être collecté.", "Publication", "Ouvrir le tri"),
      ar: T("سجلات لم تُحسم بعد", "يحتاج كل سجل في الدفعة إلى قرار قبل جمعها.", "النشر", "فتح المراجعة"),
    },
  },
  BATCH_INCOMPLETE: {
    role: "unclear",
    action: "triage",
    copy: {
      en: T("A batch has a conflict", "A record with two different decisions is left out until you keep one, so its batch is incomplete.", "Publishing", "Open triage"),
      fr: T("Un lot comporte un conflit", "Une notice avec deux décisions différentes est écartée jusqu'à ce que vous en gardiez une ; son lot est donc incomplet.", "Publication", "Ouvrir le tri"),
      ar: T("دفعة فيها تعارض", "يُستبعد السجل ذو القرارين المختلفين حتى تُبقي على أحدهما، فتبقى دفعته ناقصة.", "النشر", "فتح المراجعة"),
    },
  },
  UNRESOLVED_FINALIZE_REFUSED: {
    role: "unclear",
    action: "triage",
    copy: {
      en: T("Unresolved rows", "Some rows are still unresolved. Decide them, or send them to full text.", "Publishing", "Open triage"),
      fr: T("Lignes non résolues", "Certaines lignes restent non résolues. Décidez-les ou envoyez-les au texte intégral.", "Publication", "Ouvrir le tri"),
      ar: T("صفوف غير محسومة", "ما زالت بعض الصفوف غير محسومة. احسمها أو أحِلها إلى النص الكامل.", "النشر", "فتح المراجعة"),
    },
  },
  PROVENANCE_MISSING: {
    role: "blocked",
    action: "triage",
    copy: {
      en: T("Decision without provenance", "A decision lacks its screener, method or time and was refused; nothing is filled in for it.", "That decision", "Decide it again"),
      fr: T("Décision sans provenance", "Une décision sans évaluateur, méthode ou horodatage a été refusée ; rien n'est complété à sa place.", "Cette décision", "La décider à nouveau"),
      ar: T("قرار دون مصدر", "رُفض قرار يفتقد المراجع أو الطريقة أو الوقت، ولا يُملأ عنه شيء.", "ذلك القرار", "حسمه من جديد"),
    },
  },
  BATCH_MISSING: {
    role: "blocked",
    action: "prepare",
    copy: {
      en: T("Batch missing", "A batch file the engine expects is not there.", "That batch", "Prepare again"),
      fr: T("Lot manquant", "Un fichier de lot attendu par le moteur est absent.", "Ce lot", "Préparer à nouveau"),
      ar: T("دفعة مفقودة", "ملف دفعة يتوقعه المحرك غير موجود.", "تلك الدفعة", "إعادة التحضير"),
    },
  },
  APPROVAL_NOT_OPERATOR: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("Not the operator", "Approval is recorded only for the local operator of this workspace.", "Approval", "Approve from this computer"),
      fr: T("Pas l'opérateur", "L'approbation n'est enregistrée que pour l'opérateur local de cet espace.", "Approbation", "Approuver depuis cet ordinateur"),
      ar: T("لست المشغّل", "لا يُسجَّل الاعتماد إلا للمشغّل المحلي لهذه المساحة.", "الاعتماد", "الاعتماد من هذا الحاسوب"),
    },
  },
  PAIRING_CODE_INVALID: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("Wrong approval code", "The code does not match the one shown in the terminal, or it expired.", "Approval", "Type the code again"),
      fr: T("Code d'approbation erroné", "Le code ne correspond pas à celui affiché dans le terminal, ou il a expiré.", "Approbation", "Saisir le code à nouveau"),
      ar: T("رمز اعتماد خاطئ", "لا يطابق الرمز المعروض في الطرفية، أو انتهت صلاحيته.", "الاعتماد", "أعد كتابة الرمز"),
    },
  },
  ACTION_ORIGIN_REFUSED: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("Action refused from here", "Approving and publishing work only from the app on this computer.", "Approval and publishing", "Open the app on this computer"),
      fr: T("Action refusée depuis ici", "L'approbation et la publication ne fonctionnent que depuis l'application sur cet ordinateur.", "Approbation et publication", "Ouvrir l'application sur cet ordinateur"),
      ar: T("رُفض الإجراء من هنا", "لا يعمل الاعتماد والنشر إلا من التطبيق على هذا الحاسوب.", "الاعتماد والنشر", "افتح التطبيق على هذا الحاسوب"),
    },
  },
  TOKEN_SCOPE_REFUSED: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("Not available on this device", "This action is for the desktop only, or the phone's session ended.", "This action", "Use the desktop"),
      fr: T("Indisponible sur cet appareil", "Cette action est réservée au bureau, ou la session du téléphone a pris fin.", "Cette action", "Utiliser le bureau"),
      ar: T("غير متاح على هذا الجهاز", "هذا الإجراء لسطح المكتب فقط، أو انتهت جلسة الهاتف.", "هذا الإجراء", "استخدم سطح المكتب"),
    },
  },
  IDEMPOTENCY_CONFLICT: {
    role: "blocked",
    action: "reload",
    copy: {
      en: T("Event id reused", "An event id was sent again with different content and was refused.", "That decision", "Reload"),
      fr: T("Identifiant d'événement réutilisé", "Un identifiant d'événement a été renvoyé avec un autre contenu et refusé.", "Cette décision", "Recharger"),
      ar: T("أُعيد استخدام معرّف حدث", "أُرسل معرّف حدث مرة أخرى بمحتوى مختلف فرُفض.", "ذلك القرار", "إعادة التحميل"),
    },
  },
  REASON_CODE_INVALID: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("Reason not in the protocol", "An exclusion needs one of the protocol's exclusion codes, or a failed inclusion criterion.", "That decision", "Choose another reason"),
      fr: T("Motif hors protocole", "Une exclusion exige un code d'exclusion du protocole ou un critère d'inclusion non satisfait.", "Cette décision", "Choisir un autre motif"),
      ar: T("سبب خارج البروتوكول", "يحتاج الاستبعاد إلى رمز استبعاد من البروتوكول أو معيار إدراج غير مستوفى.", "ذلك القرار", "اختر سببًا آخر"),
    },
  },
  UNKNOWN_STUDY: {
    role: "blocked",
    action: "reload",
    copy: {
      en: T("Record not in the corpus", "This record is not in the accepted corpus.", "That record", "Reload"),
      fr: T("Notice hors corpus", "Cette notice ne fait pas partie du corpus accepté.", "Cette notice", "Recharger"),
      ar: T("سجل خارج المجموعة", "هذا السجل ليس ضمن المجموعة المقبولة.", "ذلك السجل", "إعادة التحميل"),
    },
  },
  PROPOSAL_HIDDEN: {
    role: "exclude",
    action: "none",
    copy: {
      en: T("Draft hidden", "Decide the record first; the agent's draft opens after.", "The agent's draft", "Decide the record"),
      fr: T("Brouillon masqué", "Décidez d'abord la notice ; le brouillon de l'agent s'ouvre ensuite.", "Le brouillon de l'agent", "Décider la notice"),
      ar: T("المسودة مخفية", "احسم السجل أولًا؛ تُفتح مسودة الوكيل بعد ذلك.", "مسودة الوكيل", "احسم السجل"),
    },
  },
};

export interface StateCopy {
  code: string;
  known: boolean;
  role: DecisionRole;
  action: StateAction;
  title: string;
  body: string;
  affects: string;
  actionLabel: string;
}

const UNKNOWN: Record<Locale, { title: string; body: string }> = {
  en: { title: "Refused", body: "The engine refused this with the code below." },
  fr: { title: "Refusé", body: "Le moteur a refusé avec le code ci-dessous." },
  ar: { title: "مرفوض", body: "رفض المحرك ذلك بالرمز أدناه." },
};

/** The card for a code; an unknown code renders as itself, never as another card. */
export function stateCopy(locale: Locale, code: string): StateCopy {
  const entry = STATES[code] ?? (code === "CONSOLE_UNREACHABLE" || code === "CONSOLE_TIMEOUT" ? STATES.ENGINE_UNREACHABLE : undefined);
  if (!entry) {
    return { code, known: false, role: "blocked", action: "none", title: UNKNOWN[locale].title, body: UNKNOWN[locale].body, affects: "", actionLabel: "" };
  }
  const c = entry.copy[locale];
  return { code, known: true, role: entry.role, action: entry.action, title: c.title, body: c.body, affects: c.affects, actionLabel: c.action };
}

export const AFFECTS_LABEL: Record<Locale, string> = { en: "Affects:", fr: "Concerne :", ar: "يؤثر في:" };
