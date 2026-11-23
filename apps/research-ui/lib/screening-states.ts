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

export type StateAction =
  | "import"
  | "prepare"
  | "proposals"
  | "triage"
  | "publish"
  | "home"
  | "retry"
  | "reload"
  | "terminal"
  | "none"
  // Phase 1 discovery (M3c-screens): links into the discovery steps and inception.
  | "harvest"
  | "discovery-import"
  | "handoff"
  | "inception"
  // M4d inception recon: a link to one inception step of this draft (the caller gives the href),
  // and running the first search again (the caller gives the handler).
  | "inception-step"
  | "explore-search";

interface StateEntry {
  role: DecisionRole;
  action: StateAction;
  /** A terminal command shown under the action, for people who prefer the terminal. */
  command?: string;
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
    action: "import",
    command: "nexus-scholar accept-corpus --ris Scopus=<file>.ris",
    copy: {
      en: T("No accepted corpus", "Batches can be prepared only from an accepted corpus. Import your search results and accept them first.", "Batch preparation only", "Import the corpus"),
      fr: T("Aucun corpus accepté", "Les lots ne peuvent être préparés qu'à partir d'un corpus accepté. Importez d'abord vos résultats de recherche et acceptez-les.", "Préparation des lots uniquement", "Importer le corpus"),
      ar: T("لا توجد مجموعة مقبولة", "لا تُحضَّر الدفعات إلا من مجموعة مقبولة. استورد نتائج بحثك واقبلها أولًا.", "تحضير الدفعات فقط", "استيراد المجموعة"),
    },
  },
  // Spec 11 (M5b): the corpus import refusals. Each affects the one file or step named.
  SOURCE_NOT_RIS: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("No records in this file", "No RIS records were found in it. Export your results from the database as RIS (.ris or .txt) and add that file.", "This file only; nothing was added", "Choose another file"),
      fr: T("Aucune notice dans ce fichier", "Aucune notice RIS n'y a été trouvée. Exportez vos résultats depuis la base au format RIS (.ris ou .txt) et ajoutez ce fichier.", "Ce fichier seulement ; rien n'a été ajouté", "Choisir un autre fichier"),
      ar: T("لا سجلات في هذا الملف", "لم يُعثر فيه على سجلات RIS. صدّر نتائجك من قاعدة البيانات بصيغة RIS ‏(.ris أو .txt) ثم أضف ذلك الملف.", "هذا الملف فقط؛ لم يُضف شيء", "اختر ملفًا آخر"),
    },
  },
  SOURCE_TOO_LARGE: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("File too large", "Files are limited to 50 MB. Export the results in parts and add each part under the same database name; the parts are added up.", "This file only; nothing was added", "Export in parts"),
      fr: T("Fichier trop volumineux", "Les fichiers sont limités à 50 Mo. Exportez les résultats en plusieurs parties et ajoutez chacune sous le même nom de base ; les parties sont additionnées.", "Ce fichier seulement ; rien n'a été ajouté", "Exporter en parties"),
      ar: T("الملف كبير جدًا", "حجم الملف محدود بـ 50 ميغابايت. صدّر النتائج على أجزاء وأضف كل جزء تحت اسم قاعدة البيانات نفسه؛ تُجمع الأجزاء.", "هذا الملف فقط؛ لم يُضف شيء", "التصدير على أجزاء"),
    },
  },
  SOURCE_DUPLICATE_FILE: {
    role: "unclear",
    action: "none",
    copy: {
      en: T("This file is already added", "The same file is already in the list, so it was not added twice.", "This file only", "Choose another file"),
      fr: T("Ce fichier est déjà ajouté", "Le même fichier figure déjà dans la liste ; il n'a pas été ajouté deux fois.", "Ce fichier seulement", "Choisir un autre fichier"),
      ar: T("هذا الملف مضاف مسبقًا", "الملف نفسه موجود في القائمة، فلم يُضف مرتين.", "هذا الملف فقط", "اختر ملفًا آخر"),
    },
  },
  SOURCE_LABEL_INVALID: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("Check the database name", "Use 1 to 40 letters, digits, spaces or . & ( ) + / - _.", "This file only; nothing was added", "Edit the name"),
      fr: T("Vérifiez le nom de la base", "Utilisez de 1 à 40 lettres, chiffres, espaces ou . & ( ) + / - _.", "Ce fichier seulement ; rien n'a été ajouté", "Modifier le nom"),
      ar: T("تحقق من اسم قاعدة البيانات", "استعمل من 1 إلى 40 حرفًا أو رقمًا أو مسافة أو . & ( ) + / - _.", "هذا الملف فقط؛ لم يُضف شيء", "عدّل الاسم"),
    },
  },
  SOURCE_DATE_INVALID: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("Check the date searched", "The date must be a calendar date (year, month, day), or left empty.", "This file only; nothing was added", "Edit the date"),
      fr: T("Vérifiez la date de recherche", "La date doit être une date du calendrier (année, mois, jour), ou rester vide.", "Ce fichier seulement ; rien n'a été ajouté", "Modifier la date"),
      ar: T("تحقق من تاريخ البحث", "يجب أن يكون التاريخ تاريخًا تقويميًا (سنة، شهر، يوم) أو أن يُترك فارغًا.", "هذا الملف فقط؛ لم يُضف شيء", "عدّل التاريخ"),
    },
  },
  SOURCE_NOT_FOUND: {
    role: "unclear",
    action: "reload",
    copy: {
      en: T("That file is no longer in the list", "It was removed already, perhaps from another tab.", "The list of files", "Reload"),
      fr: T("Ce fichier n'est plus dans la liste", "Il a déjà été retiré, peut-être depuis un autre onglet.", "La liste des fichiers", "Recharger"),
      ar: T("لم يعد هذا الملف في القائمة", "أُزيل مسبقًا، ربما من تبويب آخر.", "قائمة الملفات", "إعادة التحميل"),
    },
  },
  // M3c-screens (spec 04): since M3d-engine a browser harvest waits for the hand-off accept,
  // so the next step is the hand-off, not Prepare.
  VERIFIED_EXISTS: {
    role: "unclear",
    action: "handoff",
    copy: {
      en: T("These records have an unknown origin", "This workspace holds records whose origin the app does not know (no search and no import of this app made them), so a database export is not added to them.", "No file can be added to this workspace.", "Review these records on the Hand-off"),
      fr: T("Ces notices ont une origine inconnue", "Cet espace contient des notices dont l'application ne connaît pas l'origine (aucune recherche ni aucun import de cette application ne les a produites) ; un export de base ne leur est donc pas ajouté.", "Aucun fichier ne peut être ajouté à cet espace.", "Examiner ces notices à la remise"),
      ar: T("لهذه السجلات أصل غير معروف", "تحتوي مساحة العمل هذه على سجلات لا يعرف التطبيق أصلها (لم ينتجها أي بحث ولا أي استيراد في هذا التطبيق)، لذلك لا تُضاف إليها صادرات قواعد البيانات.", "لا يمكن إضافة أي ملف إلى مساحة العمل هذه.", "راجع هذه السجلات في التسليم"),
    },
  },
  CORPUS_ALREADY_ACCEPTED: {
    role: "include",
    action: "reload",
    copy: {
      en: T("The corpus is already frozen", "Databases can no longer be added or removed, because screening starts from this corpus.", "Adding, removing and accepting", "See what was imported"),
      fr: T("Le corpus est déjà figé", "On ne peut plus ajouter ni retirer de base, car la sélection part de ce corpus.", "Ajout, retrait et acceptation", "Voir ce qui a été importé"),
      ar: T("المجموعة مجمّدة بالفعل", "لم يعد ممكنًا إضافة قاعدة بيانات أو إزالتها، لأن الفرز يبدأ من هذه المجموعة.", "الإضافة والإزالة والقبول", "عرض ما استُورد"),
    },
  },
  NOTHING_STAGED: {
    role: "unclear",
    action: "reload",
    copy: {
      en: T("Nothing to accept yet", "Add at least one database file before you accept.", "Accepting", "Reload"),
      fr: T("Rien à accepter pour l'instant", "Ajoutez au moins un fichier de base avant d'accepter.", "L'acceptation", "Recharger"),
      ar: T("لا شيء للقبول بعد", "أضف ملف قاعدة بيانات واحدًا على الأقل قبل القبول.", "القبول", "إعادة التحميل"),
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
  // H-screening-drafts: an accepted corpus whose batches are not prepared yet (the
  // run screen said "No accepted corpus" here before).
  BATCHES_NOT_PREPARED: {
    role: "unclear",
    action: "prepare",
    copy: {
      en: T("Batches not prepared yet", "The corpus is accepted. Prepare the screening batches before an agent run or triage.", "Agent runs, triage and agreement", "Prepare batches"),
      fr: T("Lots pas encore préparés", "Le corpus est accepté. Préparez les lots de sélection avant un passage de l'agent ou le tri.", "Passages de l'agent, tri et accord", "Préparer les lots"),
      ar: T("لم تُحضَّر الدفعات بعد", "قُبلت المجموعة. حضّر دفعات الفرز قبل تشغيل الوكيل أو المراجعة.", "تشغيل الوكيل والمراجعة والاتفاق", "تحضير الدفعات"),
    },
  },
  // H-screening-drafts: a method amendment the engine refused; nothing was changed.
  METHOD_AMENDMENT_INVALID: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("The amendment was not recorded", "The engine refused this method change, and nothing was changed. The details say why.", "This change only", "Choose again or keep the value"),
      fr: T("L'amendement n'a pas été enregistré", "Le moteur a refusé ce changement de méthode, et rien n'a changé. Les détails disent pourquoi.", "Ce changement seulement", "Choisir à nouveau ou garder la valeur"),
      ar: T("لم يُسجَّل التعديل", "رفض المحرك تغيير المنهج هذا، ولم يتغير شيء. التفاصيل تذكر السبب.", "هذا التغيير فقط", "اختر من جديد أو أبقِ القيمة"),
    },
  },
  // H-adopted-decisions-disclosure: a declaration, a withdrawal or a sample's result the engine refused; nothing was recorded.
  ADOPTION_CONFIRM_REQUIRED: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("Not recorded without your confirmation", "Nothing was declared. Tick the confirmation and record it again.", "This declaration only", "Confirm, then record"),
      fr: T("Rien n'est enregistré sans votre confirmation", "Rien n'a été déclaré. Cochez la confirmation et enregistrez à nouveau.", "Cette déclaration seulement", "Confirmer, puis enregistrer"),
      ar: T("لا يُسجَّل شيء دون تأكيدك", "لم يُصرَّح بشيء. ضع علامة التأكيد ثم سجّل من جديد.", "هذا التصريح فقط", "أكّد ثم سجّل"),
    },
  },
  ADOPTION_EVENT_NOT_WINNING: {
    role: "blocked",
    action: "reload",
    copy: {
      en: T("A decision has changed since this page was read", "One of the selected decisions is no longer the record's current decision. Nothing was declared.", "This declaration only", "Reload and select again"),
      fr: T("Une décision a changé depuis la lecture de cette page", "L'une des décisions sélectionnées n'est plus la décision actuelle de la notice. Rien n'a été déclaré.", "Cette déclaration seulement", "Recharger et sélectionner à nouveau"),
      ar: T("تغيّر قرار منذ قراءة هذه الصفحة", "أحد القرارات المحدَّدة لم يعد القرار الحالي للسجل. لم يُصرَّح بشيء.", "هذا التصريح فقط", "أعد التحميل وحدّد من جديد"),
    },
  },
  ADOPTION_ALREADY_DECLARED: {
    role: "blocked",
    action: "reload",
    copy: {
      en: T("A record is already declared", "A selected record is declared already, or named twice. Nothing was declared.", "This declaration only", "Reload and select again"),
      fr: T("Une notice est déjà déclarée", "Une notice sélectionnée est déjà déclarée, ou nommée deux fois. Rien n'a été déclaré.", "Cette déclaration seulement", "Recharger et sélectionner à nouveau"),
      ar: T("سجل مصرَّح به بالفعل", "أحد السجلات المحدَّدة مصرَّح به بالفعل أو مذكور مرتين. لم يُصرَّح بشيء.", "هذا التصريح فقط", "أعد التحميل وحدّد من جديد"),
    },
  },
  ADOPTION_DECLARATION_INVALID: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("The declaration was not recorded", "Select at least one decision, and keep the note under 500 characters. Nothing was declared.", "This declaration only", "Change it and record again"),
      fr: T("La déclaration n'a pas été enregistrée", "Sélectionnez au moins une décision et gardez la note sous 500 caractères. Rien n'a été déclaré.", "Cette déclaration seulement", "Modifier et enregistrer à nouveau"),
      ar: T("لم يُسجَّل التصريح", "حدّد قرارًا واحدًا على الأقل، وأبقِ الملاحظة دون 500 حرف. لم يُصرَّح بشيء.", "هذا التصريح فقط", "عدّل ثم سجّل من جديد"),
    },
  },
  ADOPTION_NOT_DECLARED: {
    role: "blocked",
    action: "reload",
    copy: {
      en: T("That record is not declared", "It was never declared, or was withdrawn already. Nothing was recorded.", "This withdrawal only", "Reload"),
      fr: T("Cette notice n'est pas déclarée", "Elle n'a jamais été déclarée, ou a déjà été retirée. Rien n'a été enregistré.", "Ce retrait seulement", "Recharger"),
      ar: T("هذا السجل غير مصرَّح به", "لم يُصرَّح به قط، أو سُحب بالفعل. لم يُسجَّل شيء.", "هذا السحب فقط", "إعادة التحميل"),
    },
  },
  ADOPTION_SAMPLE_INVALID: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("The sample was not recorded", "The size must be between 1 and the selected exclusions, or the sample's result is already recorded, or a sampled record has no decision. The details say which.", "This sample only", "Change it and try again"),
      fr: T("L'échantillon n'a pas été enregistré", "La taille doit être comprise entre 1 et les exclusions sélectionnées, ou le résultat de l'échantillon est déjà enregistré, ou une notice de l'échantillon n'a pas de décision. Les détails disent lequel.", "Cet échantillon seulement", "Modifier et réessayer"),
      ar: T("لم تُسجَّل العيّنة", "يجب أن يكون الحجم بين 1 وعدد الاستبعادات المحدَّدة، أو أن نتيجة العيّنة مسجَّلة بالفعل، أو أن سجلًا في العيّنة بلا قرار. التفاصيل تذكر أيها.", "هذه العيّنة فقط", "عدّل وحاول من جديد"),
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
      en: T("Decision without provenance", "A decision lacks its screener, method or time, or its time is more than 5 minutes ahead of this computer's clock, and was refused; nothing is filled in for it. If the device's clock is wrong, correct it first.", "That decision", "Decide it again"),
      fr: T("Décision sans provenance", "Une décision sans évaluateur, méthode ou horodatage, ou dont l'heure dépasse de plus de 5 minutes l'horloge de cet ordinateur, a été refusée ; rien n'est complété à sa place. Si l'horloge de l'appareil est fausse, corrigez-la d'abord.", "Cette décision", "La décider à nouveau"),
      ar: T("قرار دون مصدر", "رُفض قرار يفتقد المراجع أو الطريقة أو الوقت، أو يسبق وقتُه ساعةَ هذا الحاسوب بأكثر من 5 دقائق، ولا يُملأ عنه شيء. إن كانت ساعة الجهاز خاطئة فصحّحها أولًا.", "ذلك القرار", "حسمه من جديد"),
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
      en: T("Not accepted as the approver", "The engine records approval only under a person's name, from this computer. A name such as “unknown” does not count.", "Approval", "Type your own name under Approver"),
      fr: T("Non accepté comme approbateur", "Le moteur n'enregistre une approbation que sous le nom d'une personne, depuis cet ordinateur. Un nom comme « unknown » ne compte pas.", "Approbation", "Saisir votre nom sous Approbateur"),
      ar: T("غير مقبول بوصفه المعتمِد", "لا يسجّل المحرك الاعتماد إلا باسم شخص ومن هذا الحاسوب. اسم مثل «unknown» لا يُحتسب.", "الاعتماد", "اكتب اسمك تحت المعتمِد"),
    },
  },
  OPERATOR_CONTEXT_MISSING: {
    role: "blocked",
    action: "publish",
    copy: {
      en: T("No approver name yet", "Approvals are recorded under the approver's name, and none is saved for this workspace.", "Approval", "Save your name under Approver"),
      fr: T("Pas encore de nom d'approbateur", "Les approbations sont enregistrées sous le nom de l'approbateur, et aucun n'est enregistré pour cet espace.", "Approbation", "Enregistrer votre nom sous Approbateur"),
      ar: T("لا يوجد اسم معتمِد بعد", "تُسجَّل الاعتمادات باسم المعتمِد، ولا يوجد اسم محفوظ لهذه المساحة.", "الاعتماد", "احفظ اسمك تحت المعتمِد"),
    },
  },
  APPROVAL_CONTENT_CHANGED: {
    role: "blocked",
    action: "publish",
    copy: {
      en: T("The approval no longer matches", "What would be published differs from what was approved, usually because a decision changed after the last approval. Publishing cannot repair an approval.", "Publishing", "Approve the last batch again, then publish"),
      fr: T("L'approbation ne correspond plus", "Ce qui serait publié diffère de ce qui a été approuvé, en général parce qu'une décision a changé après la dernière approbation. La publication ne peut pas réparer une approbation.", "Publication", "Approuver à nouveau le dernier lot, puis publier"),
      ar: T("لم يعد الاعتماد مطابقًا", "ما سيُنشر يختلف عمّا اعتُمد، غالبًا لأن قرارًا تغيّر بعد آخر اعتماد. لا يمكن للنشر إصلاح الاعتماد.", "النشر", "اعتمد آخر دفعة من جديد ثم انشر"),
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
  APPROVAL_WINDOW_UNAVAILABLE: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("The approval codes could not be shown", "The window that shows the approval codes could not open on this computer, and this app has no terminal to show them. No code was shown anywhere.", "Approval", "Ask for the codes again; if this keeps happening, restart Nexus Scholar"),
      fr: T("Les codes d'approbation n'ont pas pu être affichés", "La fenêtre qui affiche les codes d'approbation n'a pas pu s'ouvrir sur cet ordinateur, et cette application n'a pas de terminal pour les afficher. Aucun code n'a été affiché.", "Approbation", "Redemander les codes ; si cela se répète, redémarrer Nexus Scholar"),
      ar: T("تعذّر عرض رموز الاعتماد", "لم تتمكن النافذة التي تعرض رموز الاعتماد من الفتح على هذا الحاسوب، ولا توجد طرفية لهذا التطبيق لعرضها. لم يُعرض أي رمز.", "الاعتماد", "اطلب الرموز من جديد، وإن تكرر ذلك فأعد تشغيل Nexus Scholar"),
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
  // M6-beta (review S-P1-3): the reason must agree with the checklist answers.
  REASON_CODE_INCONSISTENT: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("The reason contradicts your answers", "The exclusion reason names a criterion you answered the other way. Change the answer or the reason.", "That decision; nothing was recorded", "Change the answer or the reason"),
      fr: T("Le motif contredit vos réponses", "Le motif d'exclusion désigne un critère auquel vous avez répondu dans l'autre sens. Modifiez la réponse ou le motif.", "Cette décision ; rien n'a été enregistré", "Modifier la réponse ou le motif"),
      ar: T("السبب يناقض إجاباتك", "يذكر سبب الاستبعاد معيارًا أجبت عنه بعكس ذلك. غيّر الإجابة أو السبب.", "ذلك القرار؛ لم يُسجَّل شيء", "غيّر الإجابة أو السبب"),
    },
  },
  // M11b (spec 13): the criteria in force and the pilot.
  REASON_CODE_RETIRED: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("That reason was replaced", "The criterion this reason names was replaced by a revision of the criteria. Choose a reason from the criteria in force.", "That decision; nothing was recorded", "Choose another reason"),
      fr: T("Ce motif a été remplacé", "Le critère que nomme ce motif a été remplacé par une révision des critères. Choisissez un motif parmi les critères en vigueur.", "Cette décision ; rien n'a été enregistré", "Choisir un autre motif"),
      ar: T("استُبدل هذا السبب", "استُبدل المعيار الذي يذكره هذا السبب بمراجعة للمعايير. اختر سببًا من المعايير السارية.", "ذلك القرار؛ لم يُسجَّل شيء", "اختر سببًا آخر"),
    },
  },
  PILOT_OPEN: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("This record is in your open pilot", "Decide it in the pilot, or end the pilot to screen it here. A new pilot is drawn only once the open one is finished.", "That decision or draw; nothing was recorded", "Go to the pilot"),
      fr: T("Cette notice est dans votre pilote en cours", "Décidez-la dans le pilote, ou arrêtez le pilote pour la trier ici. Un nouveau pilote n'est tiré qu'une fois le pilote en cours terminé.", "Cette décision ou ce tirage ; rien n'a été enregistré", "Aller au pilote"),
      ar: T("هذا السجل في تجربتك الجارية", "احسمه في التجربة، أو أنهِ التجربة لتفرزه هنا. لا تُسحب تجربة جديدة إلا بعد انتهاء الجارية.", "ذلك القرار أو السحب؛ لم يُسجَّل شيء", "اذهب إلى التجربة"),
    },
  },
  PILOT_CLOSED: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("This pilot has ended", "Its decisions are kept; no more can be added here. Its records are back in the main screening.", "That decision; nothing was recorded", "See the pilot result"),
      fr: T("Ce pilote est arrêté", "Ses décisions sont conservées ; on ne peut plus en ajouter ici. Ses notices sont revenues dans le tri principal.", "Cette décision ; rien n'a été enregistré", "Voir le résultat du pilote"),
      ar: T("انتهت هذه التجربة", "تُحفظ قراراتها، ولا يمكن إضافة المزيد هنا. عادت سجلاتها إلى الفرز الرئيسي.", "ذلك القرار؛ لم يُسجَّل شيء", "اعرض نتيجة التجربة"),
    },
  },
  PILOT_RECORD_UNKNOWN: {
    role: "blocked",
    action: "reload",
    copy: {
      en: T("This record is not in the pilot", "The pilot was drawn without this record. Reload the pilot.", "That decision; nothing was recorded", "Reload"),
      fr: T("Cette notice n'est pas dans le pilote", "Le pilote a été tiré sans cette notice. Rechargez le pilote.", "Cette décision ; rien n'a été enregistré", "Recharger"),
      ar: T("هذا السجل ليس في التجربة", "سُحبت التجربة دون هذا السجل. أعد تحميل التجربة.", "ذلك القرار؛ لم يُسجَّل شيء", "إعادة التحميل"),
    },
  },
  PILOT_NOT_FOUND: {
    role: "blocked",
    action: "home",
    copy: {
      en: T("That pilot does not exist in this workspace", "No pilot has that name here. Open the screening home to draw one.", "This page only", "Screening home"),
      fr: T("Ce pilote n'existe pas dans cet espace de travail", "Aucun pilote ne porte ce nom ici. Ouvrez l'accueil du tri pour en tirer un.", "Cette page seulement", "Accueil du tri"),
      ar: T("هذه التجربة غير موجودة في مساحة العمل هذه", "لا توجد تجربة بهذا الاسم هنا. افتح صفحة الفرز الرئيسية لسحب واحدة.", "هذه الصفحة فقط", "صفحة الفرز الرئيسية"),
    },
  },
  PILOT_SIZE_INVALID: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("That pilot size cannot be drawn", "A pilot holds 20 to 100 records, in tens, and no more than the records with no decision that are in no earlier pilot.", "The draw; nothing was drawn", "Choose another size"),
      fr: T("Cette taille de pilote ne peut pas être tirée", "Un pilote compte de 20 à 100 notices, par dizaines, et pas plus que les notices sans décision qui ne sont dans aucun pilote antérieur.", "Le tirage ; rien n'a été tiré", "Choisir une autre taille"),
      ar: T("لا يمكن سحب تجربة بهذا الحجم", "تضم التجربة من 20 إلى 100 سجل، بالعشرات، ولا تتجاوز السجلات التي بلا قرار وليست في تجربة سابقة.", "السحب؛ لم يُسحب شيء", "اختر حجمًا آخر"),
    },
  },
  CRITERIA_AMENDMENT_AFTER_APPROVAL: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("The criteria are fixed", "A batch is already approved, so the criteria are fixed. To change them after publication, start a new screening from this protocol.", "Revisions and pilots", "None"),
      fr: T("Les critères sont figés", "Un lot est déjà approuvé, les critères sont donc figés. Pour les changer après publication, commencez un nouveau tri à partir de ce protocole.", "Révisions et pilotes", "Aucune"),
      ar: T("المعايير ثابتة", "اعتُمدت دفعة بالفعل، فالمعايير ثابتة. لتغييرها بعد النشر، ابدأ فرزًا جديدًا من هذا البروتوكول.", "المراجعات والتجارب", "لا شيء"),
    },
  },
  CRITERIA_AMENDMENT_NO_BATCHES: {
    role: "blocked",
    action: "prepare",
    copy: {
      en: T("Prepare the batches first", "Criteria are revised once the screening batches exist. Before that, change criteria in Inception.", "Revisions only", "Prepare"),
      fr: T("Préparez d'abord les lots", "Les critères se révisent une fois les lots de tri créés. Avant cela, modifiez les critères dans la conception.", "Révisions seulement", "Préparer"),
      ar: T("حضّر الدفعات أولًا", "تُراجع المعايير بعد وجود دفعات الفرز. قبل ذلك، غيّر المعايير في مرحلة التأسيس.", "المراجعات فقط", "التحضير"),
    },
  },
  CRITERIA_AMENDMENT_INVALID: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("This change cannot be recorded", "The engine refused this revision; its reason is below.", "This revision; nothing was recorded", "Change it"),
      fr: T("Cette modification ne peut pas être enregistrée", "Le moteur a refusé cette révision ; sa raison figure ci-dessous.", "Cette révision ; rien n'a été enregistré", "La modifier"),
      ar: T("لا يمكن تسجيل هذا التغيير", "رفض المحرك هذه المراجعة؛ السبب أدناه.", "هذه المراجعة؛ لم يُسجَّل شيء", "عدّلها"),
    },
  },
  CRITERIA_SIDE_EMPTY: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("A side would be left empty", "This would leave no inclusion or no exclusion criterion. Add one first, or choose another change.", "This revision; nothing was recorded", "Choose another change"),
      fr: T("Un côté resterait vide", "Cela ne laisserait aucun critère d'inclusion ou d'exclusion. Ajoutez-en un d'abord, ou choisissez une autre modification.", "Cette révision ; rien n'a été enregistré", "Choisir une autre modification"),
      ar: T("سيبقى جانب فارغًا", "سيترك هذا بلا معيار إدراج أو بلا معيار استبعاد. أضف معيارًا أولًا، أو اختر تغييرًا آخر.", "هذه المراجعة؛ لم يُسجَّل شيء", "اختر تغييرًا آخر"),
    },
  },
  CRITERIA_AMENDMENT_HANDOFF: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("Batches were decided outside the app", "Some batches hold decisions made through the file hand-off; a revision could not show them again, so the criteria of this screening cannot be revised. To screen under revised criteria, start a new screening from this protocol.", "Revisions and pilots", "None"),
      fr: T("Des lots ont été décidés hors de l'application", "Certains lots contiennent des décisions prises par l'échange de fichiers ; une révision ne pourrait pas les présenter à nouveau, les critères de ce tri ne peuvent donc pas être révisés. Pour trier selon des critères révisés, commencez un nouveau tri à partir de ce protocole.", "Révisions et pilotes", "Aucune"),
      ar: T("حُسمت دفعات خارج التطبيق", "تضم بعض الدفعات قرارات اتُّخذت عبر تبادل الملفات؛ لا يمكن لمراجعة أن تعرضها مجددًا، فلا يمكن مراجعة معايير هذا الفرز. للفرز وفق معايير مُراجَعة، ابدأ فرزًا جديدًا من هذا البروتوكول.", "المراجعات والتجارب", "لا شيء"),
    },
  },
  // M7-method (spec 02 amendment 2026-11-08): the protocol's method block.
  BLINDING_SET_BY_PROTOCOL: {
    role: "blocked",
    action: "reload",
    copy: {
      en: T("Set by your protocol", "Your protocol sets this. Change it on Prepare, where the change is recorded as an amendment.", "The draft setting", "Reload"),
      fr: T("Défini par votre protocole", "Votre protocole fixe ce réglage. Changez-le dans Préparer, où le changement est enregistré comme amendement.", "Le réglage du brouillon", "Recharger"),
      ar: T("محدَّد في بروتوكولك", "يحدد بروتوكولك هذا الإعداد. غيّره في التحضير، حيث يُسجَّل التغيير كتعديل.", "إعداد المسودة", "إعادة التحميل"),
    },
  },
  PROTOCOL_METHOD_INVALID: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("The protocol's method values are out of range", "A value in the protocol's method block is outside what the engine accepts. Correct protocol.json; the details name the value.", "Dedup, screening rules and the methods paragraph", "Correct the protocol"),
      fr: T("Les valeurs de méthode du protocole sont hors limites", "Une valeur du bloc de méthode du protocole sort de ce que le moteur accepte. Corrigez protocol.json ; les détails nomment la valeur.", "Dédoublonnage, règles de tri et paragraphe de méthode", "Corriger le protocole"),
      ar: T("قيم المنهج في البروتوكول خارج الحدود", "قيمة في كتلة المنهج في البروتوكول خارج ما يقبله المحرك. صحّح protocol.json؛ التفاصيل تذكر القيمة.", "إزالة التكرار وقواعد الفرز وفقرة المنهج", "صحّح البروتوكول"),
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
  CONSENT_REQUIRED: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("Consent needed", "Nothing is sent to the provider until you tick the consent box for it.", "This agent run", "Tick the consent box"),
      fr: T("Consentement requis", "Rien n'est envoyé au fournisseur tant que vous n'avez pas coché la case de consentement.", "Ce passage de l'agent", "Cocher la case de consentement"),
      ar: T("الموافقة مطلوبة", "لا يُرسل شيء إلى المزوّد حتى تحدد خانة الموافقة الخاصة به.", "تشغيل الوكيل هذا", "حدد خانة الموافقة"),
    },
  },
  PROVIDER_KEY_MISSING: {
    role: "blocked",
    action: "terminal",
    copy: {
      en: T("No key for this provider", "The key is set in the engine's terminal and kept in the system keychain; the browser never takes it.", "Agent runs with this provider", "nexus-scholar keys set <provider>"),
      fr: T("Aucune clé pour ce fournisseur", "La clé se saisit dans le terminal du moteur et reste dans le trousseau du système ; le navigateur ne la reçoit jamais.", "Les passages de l'agent avec ce fournisseur", "nexus-scholar keys set <provider>"),
      ar: T("لا مفتاح لهذا المزوّد", "يُدخَل المفتاح في طرفية المحرك ويُحفظ في سلسلة مفاتيح النظام، ولا يستلمه المتصفح أبدًا.", "تشغيلات الوكيل مع هذا المزوّد", "nexus-scholar keys set <provider>"),
    },
  },
  DRIVER_UNAVAILABLE: {
    role: "blocked",
    action: "terminal",
    copy: {
      en: T("This provider cannot be used yet", "Its driver is not installed in the engine, or a setting it needs, such as the base URL, is missing. Nothing was sent.", "Agent runs with this provider", "uv sync --extra ai"),
      fr: T("Ce fournisseur n'est pas encore utilisable", "Son pilote n'est pas installé dans le moteur, ou un réglage requis, comme l'URL de base, manque. Rien n'a été envoyé.", "Les passages de l'agent avec ce fournisseur", "uv sync --extra ai"),
      ar: T("لا يمكن استخدام هذا المزوّد بعد", "برنامج تشغيله غير مثبّت في المحرك، أو ينقصه إعداد مطلوب مثل عنوان URL الأساسي. لم يُرسَل شيء.", "تشغيلات الوكيل مع هذا المزوّد", "uv sync --extra ai"),
    },
  },
  CEILING_NOT_PRICED: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("This model's cost cannot be measured", "It has no price on file, so a cost ceiling cannot be enforced. Run it without a ceiling, or pick a priced model.", "This run", "Remove the ceiling"),
      fr: T("Le coût de ce modèle ne peut pas être mesuré", "Il n'a aucun prix enregistré : un plafond de coût ne peut pas être appliqué. Lancez-le sans plafond, ou choisissez un modèle tarifé.", "Ce passage", "Retirer le plafond"),
      ar: T("لا يمكن قياس تكلفة هذا النموذج", "لا سعر مسجّل له، فلا يمكن فرض سقف للتكلفة. شغّله دون سقف أو اختر نموذجًا مسعّرًا.", "هذا التشغيل", "إزالة السقف"),
    },
  },
  WORKSPACE_TITLE_INVALID: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("That title cannot name a folder", "It has no letters or digits to make a folder name from. Use a longer title.", "Creating this workspace", "Change the title"),
      fr: T("Ce titre ne peut pas nommer un dossier", "Il ne contient ni lettre ni chiffre pour former un nom de dossier. Utilisez un titre plus long.", "La création de cet espace", "Modifier le titre"),
      ar: T("لا يصلح هذا العنوان اسمًا لمجلد", "لا يحتوي على حروف أو أرقام تكفي لاسم مجلد. استخدم عنوانًا أطول.", "إنشاء مساحة العمل هذه", "تعديل العنوان"),
    },
  },
  WORKSPACE_EXISTS: {
    role: "unclear",
    action: "none",
    copy: {
      en: T("A workspace for this title already exists", "Its folder is already in the workspaces folder. Open it, or choose another title.", "Creating this workspace", "Choose another title"),
      fr: T("Un espace existe déjà pour ce titre", "Son dossier est déjà dans le dossier des espaces. Ouvrez-le, ou choisissez un autre titre.", "La création de cet espace", "Choisir un autre titre"),
      ar: T("توجد مساحة عمل بهذا العنوان", "مجلدها موجود في مجلد مساحات العمل. افتحها أو اختر عنوانًا آخر.", "إنشاء مساحة العمل هذه", "اختيار عنوان آخر"),
    },
  },
  WORKSPACE_PATH_REFUSED: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("That folder is outside the workspaces folder", "Only folders directly inside the workspaces folder can be created or opened here.", "This workspace", "Choose another"),
      fr: T("Ce dossier est hors du dossier des espaces", "Seuls les dossiers placés directement dans le dossier des espaces peuvent être créés ou ouverts ici.", "Cet espace", "En choisir un autre"),
      ar: T("هذا المجلد خارج مجلد مساحات العمل", "لا يمكن هنا إنشاء أو فتح إلا المجلدات الموجودة مباشرة داخل مجلد مساحات العمل.", "مساحة العمل هذه", "اختيار غيرها"),
    },
  },
  WORKSPACE_ROOT_UNAVAILABLE: {
    role: "blocked",
    action: "retry",
    copy: {
      en: T("The workspaces folder cannot be used", "It cannot be read or written, or the new workspace could not be written there. The reason is below.", "Listing and creating workspaces", "Try again"),
      fr: T("Le dossier des espaces est inutilisable", "Il ne peut être lu ou écrit, ou le nouvel espace n'a pas pu y être écrit. La raison figure ci-dessous.", "La liste et la création des espaces", "Réessayer"),
      ar: T("تعذّر استخدام مجلد مساحات العمل", "لا يمكن قراءته أو الكتابة فيه، أو تعذّرت كتابة مساحة العمل الجديدة فيه. السبب أدناه.", "عرض مساحات العمل وإنشاؤها", "إعادة المحاولة"),
    },
  },
  WORKSPACE_NOT_VALID: {
    role: "blocked",
    action: "reload",
    copy: {
      en: T("Not a Nexus Scholar workspace", "This folder lacks a workspace file, or it no longer exists. Choose another workspace.", "Opening this workspace", "Reload the list"),
      fr: T("Pas un espace Nexus Scholar", "Il manque à ce dossier un fichier d'espace, ou il n'existe plus. Choisissez un autre espace.", "L'ouverture de cet espace", "Recharger la liste"),
      ar: T("ليست مساحة عمل Nexus Scholar", "ينقص هذا المجلد ملف من ملفات مساحة العمل، أو لم يعد موجودًا. اختر مساحة عمل أخرى.", "فتح مساحة العمل هذه", "إعادة تحميل القائمة"),
    },
  },
  WORKSPACE_BUSY: {
    role: "unclear",
    action: "home",
    copy: {
      en: T("Work in progress would be stopped", "Opening another workspace restarts the app, which would end the agent run or the open approval in this one. Finish or cancel it first.", "Opening another workspace", "Go to screening home"),
      fr: T("Un travail en cours serait interrompu", "Ouvrir un autre espace redémarre l'application, ce qui mettrait fin au passage de l'agent ou à l'approbation ouverte ici. Terminez-les ou annulez-les d'abord.", "L'ouverture d'un autre espace", "Aller à l'accueil de la sélection"),
      ar: T("سيتوقف عمل جارٍ", "فتح مساحة عمل أخرى يعيد تشغيل التطبيق، فينهي تشغيل الوكيل أو الموافقة المفتوحة هنا. أكمِلهما أو ألغِهما أولًا.", "فتح مساحة عمل أخرى", "الانتقال إلى صفحة الفرز الرئيسية"),
    },
  },
  RESTART_UNSUPPORTED: {
    role: "blocked",
    action: "terminal",
    copy: {
      en: T("This app cannot switch workspaces", "It was not started with `nexus-scholar ui`, so it cannot restart on another folder. Start it from the terminal instead.", "Opening another workspace", "nexus-scholar ui"),
      fr: T("Cette application ne peut pas changer d'espace", "Elle n'a pas été lancée avec `nexus-scholar ui` et ne peut donc pas redémarrer sur un autre dossier. Lancez-la depuis le terminal.", "L'ouverture d'un autre espace", "nexus-scholar ui"),
      ar: T("لا يستطيع هذا التطبيق تبديل مساحة العمل", "لم يُشغَّل بالأمر `nexus-scholar ui`، فلا يمكنه إعادة التشغيل على مجلد آخر. شغّله من الطرفية بدلًا من ذلك.", "فتح مساحة عمل أخرى", "nexus-scholar ui"),
    },
  },
  RUN_ALREADY_ACTIVE: {
    role: "unclear",
    action: "reload",
    copy: {
      en: T("A run is already going", "One agent run per workspace at a time. Wait for it, or cancel it.", "Starting another run", "Show the active run"),
      fr: T("Un passage est déjà en cours", "Un seul passage de l'agent à la fois par espace. Attendez-le ou annulez-le.", "Le lancement d'un autre passage", "Afficher le passage en cours"),
      ar: T("تشغيل جارٍ بالفعل", "تشغيل واحد للوكيل في كل مساحة في آن واحد. انتظره أو ألغه.", "بدء تشغيل آخر", "عرض التشغيل الجاري"),
    },
  },
  COST_CEILING_REACHED: {
    role: "unclear",
    action: "none",
    copy: {
      en: T("Cost ceiling reached", "The run stops at the ceiling you set. Drafts already made are kept; the rest stay in your queue without one.", "The rest of this run", "Raise the ceiling to resume"),
      fr: T("Plafond de coût atteint", "Le passage s'arrête au plafond fixé. Les brouillons déjà faits sont conservés ; les autres notices restent dans votre file sans brouillon.", "La suite de ce passage", "Relever le plafond pour reprendre"),
      ar: T("بلغ سقف التكلفة", "يتوقف التشغيل عند السقف الذي حددته. تُحفظ المسودات المنجزة، وتبقى البقية في قائمتك دون مسودة.", "بقية هذا التشغيل", "ارفع السقف للاستئناف"),
    },
  },
  UNKNOWN_RUN: {
    role: "blocked",
    action: "reload",
    copy: {
      en: T("Run not found", "This workspace has no agent run with that id.", "That run", "Reload"),
      fr: T("Passage introuvable", "Cet espace n'a aucun passage de l'agent avec cet identifiant.", "Ce passage", "Recharger"),
      ar: T("التشغيل غير موجود", "لا يوجد في هذه المساحة تشغيل للوكيل بهذا المعرّف.", "ذلك التشغيل", "إعادة التحميل"),
    },
  },
  // Export and methods (spec 10).
  EXPORT_NOT_PUBLISHED: {
    role: "exclude",
    action: "publish",
    copy: {
      en: T("Nothing is published yet", "The screening is not published yet. Approve and publish it first.", "Export and the methods paragraph", "Go to Publish"),
      fr: T("Rien n'est encore publié", "La sélection n'est pas encore publiée. Approuvez-la et publiez-la d'abord.", "L'export et le paragraphe de méthodes", "Aller à Publier"),
      ar: T("لم يُنشر شيء بعد", "لم يُنشر الفرز بعد. وافق عليه وانشره أولًا.", "التصدير وفقرة المنهجية", "الانتقال إلى النشر"),
    },
  },
  GENERATION_STALE: {
    role: "blocked",
    action: "publish",
    copy: {
      en: T("Changed since publication", "The screening changed after it was published. Publish again before you export.", "Export and the methods paragraph", "Go to Publish"),
      fr: T("Modifiée depuis la publication", "La sélection a changé après sa publication. Publiez de nouveau avant d'exporter.", "L'export et le paragraphe de méthodes", "Aller à Publier"),
      ar: T("تغيّر منذ النشر", "تغيّر الفرز بعد نشره. انشره مجددًا قبل التصدير.", "التصدير وفقرة المنهجية", "الانتقال إلى النشر"),
    },
  },
  GENERATION_SUPERSEDED: {
    role: "unclear",
    action: "reload",
    copy: {
      en: T("A newer publication exists", "A newer generation replaced this one. Reload the page to use the current one.", "Export and the methods paragraph", "Reload"),
      fr: T("Une publication plus récente existe", "Une génération plus récente a remplacé celle-ci. Rechargez la page pour utiliser l'actuelle.", "L'export et le paragraphe de méthodes", "Recharger"),
      ar: T("يوجد نشر أحدث", "حلّ جيل أحدث محل هذا الجيل. أعد تحميل الصفحة لاستخدام الحالي.", "التصدير وفقرة المنهجية", "إعادة التحميل"),
    },
  },
  EXPORT_FORMAT_INVALID: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("Format not available", "That format is not available. Choose RIS or CSV.", "This download", "Choose RIS or CSV"),
      fr: T("Format indisponible", "Ce format n'est pas disponible. Choisissez RIS ou CSV.", "Ce téléchargement", "Choisir RIS ou CSV"),
      ar: T("الصيغة غير متاحة", "هذه الصيغة غير متاحة. اختر RIS أو CSV.", "هذا التنزيل", "اختر RIS أو CSV"),
    },
  },
  EXPORT_SOURCE_MISMATCH: {
    role: "blocked",
    action: "publish",
    copy: {
      en: T("A published file changed", "A published file no longer matches its recorded digest, so nothing was exported.", "Export and the methods paragraph", "Publish again"),
      fr: T("Un fichier publié a changé", "Un fichier publié ne correspond plus à son empreinte enregistrée ; rien n'a été exporté.", "L'export et le paragraphe de méthodes", "Publier de nouveau"),
      ar: T("تغيّر ملف منشور", "لم يعد ملف منشور يطابق بصمته المسجلة، لذا لم يُصدَّر شيء.", "التصدير وفقرة المنهجية", "النشر مجددًا"),
    },
  },
  METHODS_SOURCE_MISSING: {
    role: "blocked",
    action: "publish",
    copy: {
      en: T("A file the paragraph needs is missing", "The methods paragraph is not written with a guessed value. The missing file is named below.", "The methods paragraph", "Publish again"),
      fr: T("Un fichier nécessaire au paragraphe manque", "Le paragraphe de méthodes n'est pas rédigé avec une valeur devinée. Le fichier manquant est nommé ci-dessous.", "Le paragraphe de méthodes", "Publier de nouveau"),
      ar: T("ملف تحتاجه الفقرة مفقود", "لا تُكتب فقرة المنهجية بقيمة مخمَّنة. اسم الملف المفقود أدناه.", "فقرة المنهجية", "النشر مجددًا"),
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
  // Phase 0 inception (M4b, specs 01–08): the inception API's refusals.
  DRAFT_CONFLICT: {
    role: "unclear",
    action: "reload",
    copy: {
      en: T("This draft was saved somewhere else", "It changed since this page read it, perhaps in another tab or from the terminal. Nothing was overwritten. Reload the saved draft, then make your change again.", "Saving this draft", "Reload the saved draft"),
      fr: T("Ce brouillon a été enregistré ailleurs", "Il a changé depuis que cette page l'a lu, peut-être dans un autre onglet ou depuis le terminal. Rien n'a été écrasé. Rechargez le brouillon enregistré, puis refaites votre modification.", "L'enregistrement de ce brouillon", "Recharger le brouillon enregistré"),
      ar: T("حُفظت هذه المسودة في مكان آخر", "تغيّرت منذ أن قرأتها هذه الصفحة، ربما في تبويب آخر أو من الطرفية. لم يُستبدل شيء. أعد تحميل المسودة المحفوظة ثم أعد تعديلك.", "حفظ هذه المسودة", "إعادة تحميل المسودة المحفوظة"),
    },
  },
  DRAFT_EMITTED: {
    role: "include",
    action: "none",
    copy: {
      en: T("This draft already created a workspace", "A draft creates one workspace and is then closed, so it can no longer be changed. Start a new review to make another.", "Changing this draft", "See what was created"),
      fr: T("Ce brouillon a déjà créé un espace", "Un brouillon crée un seul espace puis se ferme ; il ne peut plus être modifié. Commencez une nouvelle revue pour en créer un autre.", "La modification de ce brouillon", "Voir ce qui a été créé"),
      ar: T("أنشأت هذه المسودة مساحة عمل بالفعل", "تُنشئ المسودة مساحة عمل واحدة ثم تُغلق، فلا يمكن تعديلها بعد ذلك. ابدأ مراجعة جديدة لإنشاء غيرها.", "تعديل هذه المسودة", "عرض ما أُنشئ"),
    },
  },
  DRAFT_NOT_FOUND: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("This draft is not here", "No draft with this id is under the workspaces folder. It may belong to another folder, or the link is wrong.", "This draft", "Go to all drafts"),
      fr: T("Ce brouillon est introuvable", "Aucun brouillon avec cet identifiant n'est dans le dossier des espaces. Il appartient peut-être à un autre dossier, ou le lien est erroné.", "Ce brouillon", "Aller à tous les brouillons"),
      ar: T("هذه المسودة غير موجودة", "لا توجد مسودة بهذا المعرّف في مجلد مساحات العمل. ربما تتبع مجلدًا آخر، أو أن الرابط خاطئ.", "هذه المسودة", "الانتقال إلى كل المسودات"),
    },
  },
  DRAFT_ID_INVALID: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("This is not a draft id", "A draft id starts with rec_ followed by 32 letters and digits. Open the draft from the list instead.", "This draft", "Go to all drafts"),
      fr: T("Ce n'est pas un identifiant de brouillon", "Un identifiant commence par rec_ suivi de 32 lettres et chiffres. Ouvrez plutôt le brouillon depuis la liste.", "Ce brouillon", "Aller à tous les brouillons"),
      ar: T("هذا ليس معرّف مسودة", "يبدأ معرّف المسودة بـ rec_ يليه 32 حرفًا ورقمًا. افتح المسودة من القائمة بدلًا من ذلك.", "هذه المسودة", "الانتقال إلى كل المسودات"),
    },
  },
  DRAFT_UNREADABLE: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("This draft cannot be read", "Its file is damaged or was edited by hand. It is kept as it is; start a new review, or repair the file.", "This draft", "Go to all drafts"),
      fr: T("Ce brouillon est illisible", "Son fichier est endommagé ou a été modifié à la main. Il est conservé tel quel ; commencez une nouvelle revue, ou réparez le fichier.", "Ce brouillon", "Aller à tous les brouillons"),
      ar: T("تتعذّر قراءة هذه المسودة", "ملفها تالف أو عُدّل يدويًا. يُترك كما هو؛ ابدأ مراجعة جديدة أو أصلح الملف.", "هذه المسودة", "الانتقال إلى كل المسودات"),
    },
  },
  DRAFT_EXISTS: {
    role: "unclear",
    action: "reload",
    copy: {
      en: T("A draft with this id already exists", "Two drafts cannot share an id. Reload to see the drafts that exist.", "Starting a draft", "Reload"),
      fr: T("Un brouillon avec cet identifiant existe déjà", "Deux brouillons ne peuvent pas partager un identifiant. Rechargez pour voir les brouillons existants.", "Le démarrage d'un brouillon", "Recharger"),
      ar: T("توجد مسودة بهذا المعرّف", "لا يمكن لمسودتين أن تتشاركا معرّفًا. أعد التحميل لترى المسودات الموجودة.", "بدء مسودة", "إعادة التحميل"),
    },
  },
  DRAFT_INVALID: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("The engine did not accept an answer", "One answer has the wrong form, for example a year that is not a number, or a lens or playbook the engine does not know. The engine's reason is below.", "Saving this draft", "Correct the answer"),
      fr: T("Le moteur n'a pas accepté une réponse", "Une réponse n'a pas la bonne forme, par exemple une année qui n'est pas un nombre, ou une perspective ou une méthode que le moteur ne connaît pas. La raison du moteur figure ci-dessous.", "L'enregistrement de ce brouillon", "Corriger la réponse"),
      ar: T("لم يقبل المحرك إحدى الإجابات", "إحدى الإجابات بصيغة خاطئة، مثل سنة ليست رقمًا، أو منظور أو منهج لا يعرفه المحرك. سبب المحرك أدناه.", "حفظ هذه المسودة", "صحّح الإجابة"),
    },
  },
  DRAFT_TOO_LARGE: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("The draft is over its size limits", "An answer is longer than the engine keeps, or a list has more entries than it keeps: 2,000 characters for a topic or a question, 200 for a name or a concept, 20 research questions, 50 concepts. Nothing was saved. The engine names the field below.", "Saving this draft", "Shorten the answer named"),
      fr: T("Le brouillon dépasse ses limites de taille", "Une réponse est plus longue que ce que le moteur conserve, ou une liste compte plus d'entrées qu'il n'en garde : 2 000 caractères pour un sujet ou une question, 200 pour un nom ou un concept, 20 questions de recherche, 50 concepts. Rien n'a été enregistré. Le moteur nomme le champ ci-dessous.", "L'enregistrement de ce brouillon", "Raccourcir la réponse nommée"),
      ar: T("المسودة تتجاوز حدود حجمها", "إحدى الإجابات أطول مما يحتفظ به المحرك، أو تضم قائمة مدخلات أكثر مما يحتفظ به: 2000 حرف للموضوع أو السؤال، و200 حرف للاسم أو المفهوم، و20 سؤال بحث، و50 مفهومًا. لم يُحفظ شيء. يذكر المحرك الحقل أدناه.", "حفظ هذه المسودة", "اختصر الإجابة المذكورة"),
    },
  },
  DRAFT_INCOMPLETE: {
    role: "unclear",
    action: "none",
    copy: {
      en: T("A few answers are still missing", "The engine needs the answers listed below before it can propose this step.", "This step only; your answers are kept", "Answer them"),
      fr: T("Il manque encore quelques réponses", "Le moteur a besoin des réponses listées ci-dessous avant de proposer cette étape.", "Cette étape seulement ; vos réponses sont conservées", "Y répondre"),
      ar: T("ما زالت بعض الإجابات ناقصة", "يحتاج المحرك إلى الإجابات المذكورة أدناه قبل أن يقترح هذه الخطوة.", "هذه الخطوة فقط؛ تُحفظ إجاباتك", "أجب عنها"),
    },
  },
  STEP_UNKNOWN: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("The engine does not know this step", "This app and the engine are different versions. Update the app.", "This step", "Update the app"),
      fr: T("Le moteur ne connaît pas cette étape", "L'application et le moteur ne sont pas de la même version. Mettez l'application à jour.", "Cette étape", "Mettre à jour l'application"),
      ar: T("لا يعرف المحرك هذه الخطوة", "التطبيق والمحرك بإصدارين مختلفين. حدّث التطبيق.", "هذه الخطوة", "تحديث التطبيق"),
    },
  },
  CRITERIA_UNDECIDED: {
    role: "unclear",
    action: "none",
    copy: {
      en: T("Some criteria still wait for your decision", "Every criterion the wizard wrote must be accepted or rejected before the protocol can be compiled.", "Review and creating the workspace", "Decide them on Concepts and criteria"),
      fr: T("Des critères attendent encore votre décision", "Chaque critère écrit par l'assistant doit être accepté ou rejeté avant de compiler le protocole.", "La vérification et la création de l'espace", "Les décider dans Concepts et critères"),
      ar: T("ما زالت بعض المعايير بانتظار قرارك", "يجب قبول كل معيار كتبه المعالج أو رفضه قبل تجميع البروتوكول.", "المراجعة وإنشاء مساحة العمل", "احسمها في المفاهيم والمعايير"),
    },
  },
  // M11b part D (spec 11): Review's preview and genesis refuse a draft whose not-reported rule is unchosen.
  METHOD_RULE_UNCHOSEN: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("Choose what the agent should do when a criterion is not reported", "There is no default: the rule decides whether a record whose abstract is silent on a criterion is marked Unclear or excluded, and it is signed into the protocol.", "Review and creating the workspace", "Choose a rule on Concepts and criteria"),
      fr: T("Choisissez ce que doit faire l'agent quand un critère n'est pas rapporté", "Il n'y a pas de valeur par défaut : la règle décide si une notice dont le résumé ne dit rien d'un critère est marquée Incertain ou exclue, et elle est signée dans le protocole.", "La vérification et la création de l'espace", "Choisir une règle dans Concepts et critères"),
      ar: T("اختر ما يفعله الوكيل حين لا يُذكر معيار", "لا قيمة افتراضية: تقرر القاعدة إن كان السجل الذي يسكت ملخصه عن معيار يوضع غير واضح أو يُستبعد، وتُوقَّع في البروتوكول.", "المراجعة وإنشاء مساحة العمل", "اختر قاعدة في المفاهيم والمعايير"),
    },
  },
  CRITERIA_MISSING: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("The protocol needs both kinds of criteria", "Accept at least one inclusion and one exclusion criterion.", "Review and creating the workspace", "Add them on Concepts and criteria"),
      fr: T("Le protocole a besoin des deux types de critères", "Acceptez au moins un critère d'inclusion et un critère d'exclusion.", "La vérification et la création de l'espace", "Les ajouter dans Concepts et critères"),
      ar: T("يحتاج البروتوكول إلى نوعي المعايير", "اقبل معيار إدراج واحدًا على الأقل ومعيار استبعاد واحدًا.", "المراجعة وإنشاء مساحة العمل", "أضفها في المفاهيم والمعايير"),
    },
  },
  INTENT_INVALID: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("The protocol compiler refused these answers", "The answers make a protocol the compiler cannot accept. Its reasons are below; correct the answers they name.", "Review and creating the workspace", "Correct the answers"),
      fr: T("Le compilateur du protocole a refusé ces réponses", "Les réponses forment un protocole que le compilateur ne peut pas accepter. Ses raisons figurent ci-dessous ; corrigez les réponses qu'elles nomment.", "La vérification et la création de l'espace", "Corriger les réponses"),
      ar: T("رفض مُجمِّع البروتوكول هذه الإجابات", "تُكوِّن الإجابات بروتوكولًا لا يقبله المُجمِّع. أسبابه أدناه؛ صحّح الإجابات التي يذكرها.", "المراجعة وإنشاء مساحة العمل", "صحّح الإجابات"),
    },
  },
  SCREENING_BOUND: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("Screening was done under the current protocol", "Replacing the protocol would leave those decisions pointing at criteria that no longer exist. Type the workspace name to confirm, or keep the protocol.", "Replacing this workspace's protocol", "Type the workspace name"),
      fr: T("Une sélection a été faite sous le protocole actuel", "Remplacer le protocole laisserait ces décisions pointer vers des critères qui n'existent plus. Saisissez le nom de l'espace pour confirmer, ou gardez le protocole.", "Le remplacement du protocole de cet espace", "Saisir le nom de l'espace"),
      ar: T("جرى فرز وفق البروتوكول الحالي", "استبدال البروتوكول سيترك تلك القرارات تشير إلى معايير لم تعد موجودة. اكتب اسم مساحة العمل للتأكيد، أو أبقِ البروتوكول.", "استبدال بروتوكول مساحة العمل هذه", "اكتب اسم مساحة العمل"),
    },
  },
  CONFIRMATION_MISMATCH: {
    role: "unclear",
    action: "none",
    copy: {
      en: T("The name does not match", "Type the workspace name exactly as shown to replace its protocol. Nothing was changed.", "Replacing this workspace's protocol", "Type it again"),
      fr: T("Le nom ne correspond pas", "Saisissez le nom de l'espace exactement comme affiché pour remplacer son protocole. Rien n'a été modifié.", "Le remplacement du protocole de cet espace", "Le saisir à nouveau"),
      ar: T("الاسم غير مطابق", "اكتب اسم مساحة العمل كما يظهر تمامًا لاستبدال بروتوكولها. لم يتغير شيء.", "استبدال بروتوكول مساحة العمل هذه", "اكتبه مجددًا"),
    },
  },
  // M4d (F1): genesis with replace refuses while a job runs, and reports an archive that stopped part way.
  WORKSPACE_JOB_ACTIVE: {
    role: "unclear",
    action: "none",
    copy: {
      en: T("A job is still running in this workspace", "A discovery or console job is working in the workspace, so its protocol cannot be replaced now. Nothing was moved. The job is named under Details.", "Replacing this workspace's protocol", "Wait for the job to end or stop it, then create again"),
      fr: T("Une tâche est encore en cours dans cet espace", "Une tâche de recherche ou de la console travaille dans l'espace ; son protocole ne peut pas être remplacé maintenant. Rien n'a été déplacé. La tâche est nommée dans les détails.", "Le remplacement du protocole de cet espace", "Attendre la fin de la tâche ou l'arrêter, puis créer à nouveau"),
      ar: T("ما زالت مهمة قيد التشغيل في مساحة العمل هذه", "تعمل مهمة استكشاف أو مهمة من وحدة التحكم في مساحة العمل، فلا يمكن استبدال بروتوكولها الآن. لم يُنقل شيء. اسم المهمة في التفاصيل.", "استبدال بروتوكول مساحة العمل هذه", "انتظر انتهاء المهمة أو أوقفها، ثم أنشئ مجددًا"),
    },
  },
  ARCHIVE_INCOMPLETE: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("Archiving the old corpus stopped part way", "Some files were moved to the backup folder and some were not, so the protocol was not replaced. The journal records it. The backup folder and both lists are under Details.", "Replacing this workspace's protocol", "Close the program holding the file, then try again"),
      fr: T("L'archivage de l'ancien corpus s'est arrêté en cours de route", "Certains fichiers ont été déplacés dans le dossier de sauvegarde et d'autres non ; le protocole n'a donc pas été remplacé. Le journal l'enregistre. Le dossier de sauvegarde et les deux listes sont dans les détails.", "Le remplacement du protocole de cet espace", "Fermer le programme qui tient le fichier, puis réessayer"),
      ar: T("توقفت أرشفة المجموعة القديمة في منتصف الطريق", "نُقلت بعض الملفات إلى مجلد النسخ الاحتياطي ولم يُنقل بعضها، فلم يُستبدل البروتوكول. سُجّل ذلك في السجل. مجلد النسخ الاحتياطي والقائمتان في التفاصيل.", "استبدال بروتوكول مساحة العمل هذه", "أغلق البرنامج الذي يمسك الملف، ثم حاول مجددًا"),
    },
  },
  // Phase 1 discovery (M3c-screens, spec 07): the discovery routes' refusals and job errors.
  PROTOCOL_MISSING: {
    role: "blocked",
    action: "inception",
    copy: {
      en: T("There is no protocol to search with yet", "Discovery reads its question, years and limits from a frozen protocol, and this workspace has none.", "Every step of discovery", "Write the protocol in inception"),
      fr: T("Il n'y a pas encore de protocole pour chercher", "La recherche lit sa question, ses années et ses limites dans un protocole figé, et cet espace n'en a pas.", "Toutes les étapes de la recherche", "Rédiger le protocole dans l'Inception"),
      ar: T("لا يوجد بروتوكول للبحث به بعد", "يقرأ الاستكشاف سؤاله وسنواته وحدوده من بروتوكول مجمّد، ولا يوجد بروتوكول في مساحة العمل هذه.", "كل خطوات الاستكشاف", "اكتب البروتوكول في مرحلة التأسيس"),
    },
  },
  PROTOCOL_INVALID: {
    role: "blocked",
    action: "inception",
    copy: {
      en: T("The protocol cannot be read", "Its file is damaged or no longer valid, so nothing can be searched or accepted. The engine's message is under Details.", "Searching and the hand-off", "Open inception"),
      fr: T("Le protocole est illisible", "Son fichier est endommagé ou n'est plus valide ; rien ne peut être cherché ni accepté. Le message du moteur est dans les détails.", "La recherche et la remise", "Ouvrir l'Inception"),
      ar: T("تتعذر قراءة البروتوكول", "ملفه تالف أو لم يعد صالحًا، فلا يمكن البحث ولا القبول. رسالة المحرك في التفاصيل.", "البحث والتسليم", "افتح مرحلة التأسيس"),
    },
  },
  PROTOCOL_CHANGED_SINCE_RUN: {
    role: "unclear",
    action: "harvest",
    copy: {
      en: T("The protocol changed after this search", "The run searched a query, year window, language, cap or database list the protocol no longer has. Run the search again before accepting its corpus. Nothing was frozen.", "The hand-off", "Search again"),
      fr: T("Le protocole a changé après cette recherche", "L'exécution a cherché une requête, une période, une langue, un plafond ou une liste de bases que le protocole n'a plus. Relancez la recherche avant d'accepter son corpus. Rien n'a été figé.", "La remise", "Chercher à nouveau"),
      ar: T("تغيّر البروتوكول بعد هذا البحث", "بحث هذا التشغيل باستعلام أو نطاق سنوات أو لغة أو حد أو قائمة قواعد بيانات لم تعد في البروتوكول. أعد البحث قبل قبول مجموعته. لم يُجمَّد شيء.", "التسليم", "ابحث مجددًا"),
    },
  },
  // M3i-harvest-robustness: the steps after a search (duplicates, abstracts, checks) did not end.
  PREPARATION_UNFINISHED: {
    role: "unclear",
    action: "harvest",
    copy: {
      en: T("The corpus is not prepared yet", "The search finished, but the steps after it (duplicates, abstracts, checks) did not end, so there are no works to accept. Finish preparing the corpus on the Harvest screen; no database is searched again. Nothing was frozen.", "The hand-off", "Open Harvest"),
      fr: T("Le corpus n'est pas encore préparé", "La recherche est terminée, mais les étapes qui la suivent (doublons, résumés, vérifications) ne se sont pas terminées ; il n'y a donc aucun travail à accepter. Terminez la préparation du corpus dans l'écran de collecte ; aucune base n'est interrogée à nouveau. Rien n'a été figé.", "La remise", "Ouvrir la collecte"),
      ar: T("المجموعة لم تُحضَّر بعد", "انتهى البحث، لكن الخطوات التي تليه (التكرارات والملخصات والفحوص) لم تنتهِ، فلا توجد أعمال تُقبل. أكمل تحضير المجموعة في شاشة الحصاد؛ لا يُعاد البحث في أي قاعدة بيانات. لم يُجمَّد شيء.", "التسليم", "افتح الحصاد"),
    },
  },
  PREPARATION_NOT_AVAILABLE: {
    role: "unclear",
    action: "retry",
    copy: {
      en: T("There is nothing to finish for this run", "Its corpus is already prepared, a later run replaced it, its search was not kept, or its saved records cannot be read. The engine's reason is under Details. Nothing was changed.", "Finishing this run", "Check again"),
      fr: T("Il n'y a rien à terminer pour cette exécution", "Son corpus est déjà préparé, une exécution ultérieure l'a remplacée, sa recherche n'a pas été conservée, ou ses notices enregistrées sont illisibles. La raison du moteur est dans les détails. Rien n'a été modifié.", "La fin de cette exécution", "Vérifier à nouveau"),
      ar: T("لا يوجد ما يُكمَل لهذا التشغيل", "مجموعته محضَّرة بالفعل، أو حلّ محله تشغيل لاحق، أو لم يُحتفظ ببحثه، أو تتعذر قراءة سجلاته المحفوظة. سبب المحرك في التفاصيل. لم يتغير شيء.", "إكمال هذا التشغيل", "تحقق مجددًا"),
    },
  },
  // Review F2 (decision 2026-11-12): a flag on /summary and /queue, not a
  // refusal; Home shows it instead of a queue that starts over.
  PROTOCOL_CHANGED_SINCE_BATCH: {
    role: "unclear",
    action: "inception",
    copy: {
      en: T("The protocol changed after screening started", "protocol.json no longer matches the protocol the batches were prepared under, so the decisions made under it count nowhere and every record shows as undecided. Nothing was deleted: undo the edit to see them again, or replace the protocol in Inception, which archives this screening and starts clean.", "Triage, the counts and publishing", "Open inception"),
      fr: T("Le protocole a changé après le début de la sélection", "protocol.json ne correspond plus au protocole sous lequel les lots ont été préparés : les décisions prises sous ce protocole ne comptent plus et chaque notice apparaît non décidée. Rien n'a été supprimé : annulez la modification pour les revoir, ou remplacez le protocole dans l'Inception, qui archive cette sélection et repart de zéro.", "Le tri, les comptes et la publication", "Ouvrir l'Inception"),
      ar: T("تغيّر البروتوكول بعد بدء الفرز", "لم يعد protocol.json مطابقًا للبروتوكول الذي حُضّرت الدفعات تحته، فلا تُحتسب القرارات المتخذة تحته ويظهر كل سجل غير محسوم. لم يُحذف شيء: تراجع عن التعديل لتراها من جديد، أو استبدل البروتوكول في مرحلة التأسيس التي تؤرشف هذا الفرز وتبدأ من جديد.", "المراجعة والأعداد والنشر", "افتح مرحلة التأسيس"),
    },
  },
  PROTOCOL_CHANGED_SINCE_SNAPSHOT: {
    role: "unclear",
    action: "inception",
    copy: {
      en: T("The protocol no longer matches the accepted corpus", "The workspace already froze a corpus under another protocol, and the engine will not resume on it. A changed protocol needs a new workspace.", "That search", "Open inception"),
      fr: T("Le protocole ne correspond plus au corpus accepté", "L'espace a déjà figé un corpus sous un autre protocole et le moteur ne reprendra pas dessus. Un protocole modifié demande un nouvel espace.", "Cette recherche", "Ouvrir l'Inception"),
      ar: T("لم يعد البروتوكول مطابقًا للمجموعة المقبولة", "جمّدت مساحة العمل مجموعة تحت بروتوكول آخر، ولن يستأنف المحرك عليها. البروتوكول المعدَّل يحتاج إلى مساحة عمل جديدة.", "ذلك البحث", "افتح مرحلة التأسيس"),
    },
  },
  MAILTO_NOT_SET: {
    role: "blocked",
    action: "retry",
    command: "SCHOLAR_MAILTO=<your email>",
    copy: {
      en: T("Set a contact email before searching", "A search needs a contact email for the literature databases. Put the line below in the console's environment, or in a .env file, then start the console again.", "Recall and Harvest", "Check again"),
      fr: T("Indiquez une adresse de contact avant de chercher", "Une recherche demande une adresse de contact pour les bases bibliographiques. Mettez la ligne ci-dessous dans l'environnement de la console ou dans un fichier .env, puis redémarrez la console.", "Le rappel et la collecte", "Vérifier à nouveau"),
      ar: T("حدّد بريدًا للتواصل قبل البحث", "يحتاج البحث إلى بريد للتواصل مع قواعد البيانات العلمية. ضع السطر أدناه في بيئة وحدة التحكم أو في ملف ‎.env‎، ثم أعد تشغيل وحدة التحكم.", "فحص الاستدعاء والحصاد", "تحقّق مجددًا"),
    },
  },
  OPENALEX_KEY_NOT_SET: {
    role: "blocked",
    action: "retry",
    command: "SCHOLAR_OPENALEX_KEY=<your key>",
    copy: {
      en: T("Set the OpenAlex API key before searching OpenAlex", "OpenAlex requires a free API key since February 2026. Put the line below in the console's environment, or in a .env file, then start the console again, or leave OpenAlex out of the run.", "Harvest", "Check again"),
      fr: T("Indiquez la clé d'API OpenAlex avant de chercher dans OpenAlex", "OpenAlex exige une clé d'API gratuite depuis février 2026. Mettez la ligne ci-dessous dans l'environnement de la console ou dans un fichier .env, puis redémarrez la console, ou retirez OpenAlex de l'exécution.", "La collecte", "Vérifier à nouveau"),
      ar: T("حدّد مفتاح واجهة OpenAlex البرمجية قبل البحث فيها", "تشترط OpenAlex مفتاح واجهة برمجية مجانيًا منذ فبراير 2026. ضع السطر أدناه في بيئة وحدة التحكم أو في ملف ‎.env‎، ثم أعد تشغيل وحدة التحكم، أو استبعد OpenAlex من التشغيل.", "الحصاد", "تحقّق مجددًا"),
    },
  },
  // M3g-citation-chasing (spec 09): the chase routes' refusals.
  SCREENING_NOT_PUBLISHED: {
    role: "exclude",
    action: "publish",
    copy: {
      en: T("Publish the screening first.", "Citation chasing starts from the studies you included, and those are final only once the screening is published.", "The chase", "Go to the Publish screen"),
      fr: T("Publiez d'abord la sélection.", "La chasse aux citations part des études que vous avez incluses, et celles-ci ne sont définitives qu'une fois la sélection publiée.", "La chasse", "Aller à l'écran Publier"),
      ar: T("انشر الفرز أولًا.", "تبدأ مطاردة الاستشهادات من الدراسات التي أدرجتها، ولا تكون نهائية إلا بعد نشر الفرز.", "المطاردة", "اذهب إلى شاشة النشر"),
    },
  },
  CHASE_NOT_RUN: {
    role: "unclear",
    action: "none",
    copy: {
      en: T("There is no published chase run to send.", "Run a chase first; a failed or stopped chase publishes nothing and cannot be sent.", "Sending works to screening", "Chase citations"),
      fr: T("Aucune chasse publiée à envoyer.", "Lancez d'abord une chasse ; une chasse échouée ou arrêtée ne publie rien et ne peut pas être envoyée.", "L'envoi des travaux à la sélection", "Chasser les citations"),
      ar: T("لا توجد مطاردة منشورة لإرسالها.", "شغّل مطاردة أولًا؛ المطاردة التي أخفقت أو أُوقفت لا تنشر شيئًا ولا يمكن إرسالها.", "إرسال الأعمال إلى الفرز", "طارد الاستشهادات"),
    },
  },
  CHASE_NOTHING_NEW: {
    role: "exclude",
    action: "none",
    copy: {
      en: T("The chase found nothing new.", "Everything it fetched was already in your corpus, found twice, or outside the year window, so there is no round to start.", "Sending works to screening", "Chase again"),
      fr: T("La chasse n'a rien trouvé de nouveau.", "Tout ce qu'elle a récupéré était déjà dans votre corpus, trouvé deux fois ou hors de la fenêtre d'années ; il n'y a donc pas de tour à ouvrir.", "L'envoi des travaux à la sélection", "Chasser à nouveau"),
      ar: T("لم تجد المطاردة شيئًا جديدًا.", "كل ما جلبته كان في مجموعتك بالفعل، أو وُجد مرتين، أو خارج نافذة السنوات، فلا جولة تُفتح.", "إرسال الأعمال إلى الفرز", "طارد مجددًا"),
    },
  },
  CHASE_ALREADY_ACCEPTED: {
    role: "include",
    action: "home",
    copy: {
      en: T("These works are already with screening.", "This chase run was sent to screening before; it is the finished state, not a failure.", "Sending works to screening", "Go to screening"),
      fr: T("Ces travaux sont déjà en sélection.", "Cette chasse a déjà été envoyée à la sélection ; c'est l'état final, pas une erreur.", "L'envoi des travaux à la sélection", "Aller à la sélection"),
      ar: T("هذه الأعمال في الفرز بالفعل.", "أُرسلت هذه المطاردة إلى الفرز من قبل؛ هذه هي الحالة النهائية، لا خطأ.", "إرسال الأعمال إلى الفرز", "اذهب إلى الفرز"),
    },
  },
  CHASE_STALE: {
    role: "unclear",
    action: "none",
    copy: {
      en: T("The screening changed after this chase ran.", "The screening was published again, or a later corpus was accepted, after this chase; its seeds may differ. Run the chase again.", "Sending works to screening", "Chase again"),
      fr: T("La sélection a changé après cette chasse.", "La sélection a été republiée, ou un corpus plus récent a été accepté, après cette chasse ; ses graines peuvent différer. Relancez la chasse.", "L'envoi des travaux à la sélection", "Chasser à nouveau"),
      ar: T("تغيّر الفرز بعد هذه المطاردة.", "نُشر الفرز مجددًا، أو قُبلت مجموعة أحدث، بعد هذه المطاردة؛ قد تختلف بذورها. أعد المطاردة.", "إرسال الأعمال إلى الفرز", "طارد مجددًا"),
    },
  },
  CHASE_DIRECTION_INVALID: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("Choose forward, backward or both.", "The engine chases citing works (forward), references (backward) or both; the request named another direction.", "Starting the chase", "Choose a direction"),
      fr: T("Choisissez avant, arrière ou les deux.", "Le moteur chasse les travaux citants (avant), les références (arrière) ou les deux ; la requête nommait une autre direction.", "Le lancement de la chasse", "Choisir une direction"),
      ar: T("اختر الأمام أو الخلف أو كليهما.", "يطارد المحرك الأعمال المستشهِدة (الأمام) أو المراجع (الخلف) أو كليهما؛ سمّى الطلب اتجاهًا آخر.", "بدء المطاردة", "اختر اتجاهًا"),
    },
  },
  CHASE_SEEDS_INVALID: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("The seed choice is not valid.", "Seeds are the included studies, or the included and unclear studies; the request named something else.", "Starting the chase", "Choose the seeds"),
      fr: T("Le choix des graines n'est pas valide.", "Les graines sont les études incluses, ou les études incluses et incertaines ; la requête nommait autre chose.", "Le lancement de la chasse", "Choisir les graines"),
      ar: T("اختيار البذور غير صالح.", "البذور هي الدراسات المدرجة، أو المدرجة وغير الواضحة؛ سمّى الطلب شيئًا آخر.", "بدء المطاردة", "اختر البذور"),
    },
  },
  CHASE_ACCEPT_PENDING: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("Finish sending the last chase to screening first.", "An earlier accept registered the next round's corpus but stopped before the round was archived. A new chase, or sending another chase, would build on records nobody has screened. Accept that chase again; it resumes where it stopped.", "Continuing citation chasing", "Accept the earlier chase again"),
      fr: T("Terminez d'abord l'envoi de la dernière chasse à la sélection.", "Une acceptation précédente a enregistré le corpus du tour suivant mais s'est arrêtée avant l'archivage du tour. Une nouvelle chasse, ou l'envoi d'une autre chasse, s'appuierait sur des notices que personne n'a sélectionnées. Acceptez à nouveau cette chasse ; elle reprend là où elle s'est arrêtée.", "La poursuite de la chasse aux citations", "Accepter à nouveau la chasse précédente"),
      ar: T("أكمل أولًا إرسال المطاردة الأخيرة إلى الفرز.", "سجّل قبولٌ سابق مجموعة الجولة التالية لكنه توقف قبل أرشفة الجولة. ستُبنى مطاردة جديدة، أو إرسال مطاردة أخرى، على سجلات لم يفرزها أحد. اقبل تلك المطاردة مجددًا؛ فهي تستأنف من حيث توقفت.", "مواصلة مطاردة الاستشهادات", "اقبل المطاردة السابقة مجددًا"),
    },
  },
  PROTOCOL_CHANGED_SINCE_PUBLISH: {
    role: "unclear",
    action: "home",
    copy: {
      en: T("The protocol changed after the screening was published", "Its includes no longer belong to the current protocol. Screening has to be redone and published under the current protocol before a chase can be sent. Nothing was moved.", "Sending works to screening", "Go to screening"),
      fr: T("Le protocole a changé après la publication de la sélection", "Ses inclusions n'appartiennent plus au protocole actuel. La sélection doit être refaite et publiée sous le protocole actuel avant d'envoyer une chasse. Rien n'a été déplacé.", "L'envoi des travaux à la sélection", "Aller à la sélection"),
      ar: T("تغيّر البروتوكول بعد نشر الفرز", "لم تعد إدراجاته تنتمي إلى البروتوكول الحالي. يجب إعادة الفرز ونشره تحت البروتوكول الحالي قبل إرسال مطاردة. لم يُنقل شيء.", "إرسال الأعمال إلى الفرز", "اذهب إلى الفرز"),
    },
  },
  DISCOVERY_JOB_ACTIVE: {
    role: "unclear",
    action: "none",
    copy: {
      en: T("A search is already running", "One discovery job runs at a time in a workspace. Nothing new was started.", "Starting another", "Follow the running job"),
      fr: T("Une recherche est déjà en cours", "Une seule tâche de recherche tourne à la fois dans un espace. Rien de nouveau n'a été lancé.", "Le lancement d'une autre", "Suivre la tâche en cours"),
      ar: T("يجري بحث بالفعل", "تعمل مهمة استكشاف واحدة في كل مرة داخل مساحة العمل. لم يبدأ شيء جديد.", "بدء مهمة أخرى", "تابع المهمة الجارية"),
    },
  },
  DISCOVERY_JOB_NOT_FOUND: {
    role: "unclear",
    action: "harvest",
    copy: {
      en: T("The console no longer knows this job", "The console was restarted, so this job is no longer known. If it produced a run, the run is in the run list.", "Live progress for this job", "See the run list"),
      fr: T("La console ne connaît plus cette tâche", "La console a redémarré ; cette tâche n'est plus connue. Si elle a produit une exécution, elle figure dans la liste.", "Le suivi de cette tâche", "Voir la liste des exécutions"),
      ar: T("لم تعد وحدة التحكم تعرف هذه المهمة", "أُعيد تشغيل وحدة التحكم، فلم تعد هذه المهمة معروفة. إن أنتجت تشغيلًا فهو في قائمة التشغيلات.", "متابعة هذه المهمة", "اعرض قائمة التشغيلات"),
    },
  },
  RUN_NOT_FOUND: {
    role: "exclude",
    action: "harvest",
    copy: {
      en: T("There is no such run", "No search run exists in this workspace yet, or the address names a run that is not here.", "The report", "Go to Harvest"),
      fr: T("Cette exécution n'existe pas", "Aucune recherche n'a encore été exécutée dans cet espace, ou l'adresse nomme une exécution absente.", "Le rapport", "Aller à la collecte"),
      ar: T("لا يوجد هذا التشغيل", "لا يوجد تشغيل بحث في مساحة العمل هذه بعد، أو أن العنوان يذكر تشغيلًا غير موجود.", "التقرير", "اذهب إلى الحصاد"),
    },
  },
  RECALL_NOT_RUN: {
    role: "exclude",
    action: "none",
    copy: {
      en: T("No recall check has run yet", "The page shows nothing until you run one.", "The recall table", "Run the check"),
      fr: T("Aucun contrôle de rappel n'a encore été fait", "La page n'affiche rien tant que vous n'en lancez pas un.", "Le tableau de rappel", "Lancer le contrôle"),
      ar: T("لم يُجرَ فحص استدعاء بعد", "لا تعرض الصفحة شيئًا حتى تجري فحصًا.", "جدول الاستدعاء", "أجرِ الفحص"),
    },
  },
  DEDUP_NOT_RUN: {
    role: "exclude",
    action: "harvest",
    copy: {
      en: T("No deduplication has run yet", "A search run deduplicates its records; a database export is deduplicated when you accept it.", "The duplicate counts", "Go to Harvest"),
      fr: T("Aucun dédoublonnage n'a encore été fait", "Une recherche dédoublonne ses notices ; un export de base est dédoublonné quand vous l'acceptez.", "Les comptes de doublons", "Aller à la collecte"),
      ar: T("لم تُجرَ إزالة التكرار بعد", "يزيل تشغيل البحث تكرار سجلاته؛ أما صادرات قواعد البيانات فتُزال تكراراتها عند قبولها.", "أعداد التكرارات", "اذهب إلى الحصاد"),
    },
  },
  SEEDS_INVALID: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("A seed could not be used", "Nothing was checked. One to 25 seeds, each a DOI or an arXiv id; the engine names the first one it could not use.", "The recall check", "Fix the seed named"),
      fr: T("Une graine n'a pas pu être utilisée", "Rien n'a été vérifié. De 1 à 25 graines, chacune un DOI ou un identifiant arXiv ; le moteur nomme la première qu'il n'a pas pu utiliser.", "Le contrôle de rappel", "Corriger la graine nommée"),
      ar: T("تعذّر استخدام إحدى البذور", "لم يُفحص شيء. من 1 إلى 25 بذرة، كل منها DOI أو معرّف arXiv؛ يذكر المحرك أول بذرة تعذّر استخدامها.", "فحص الاستدعاء", "صحّح البذرة المذكورة"),
    },
  },
  CAP_INVALID: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("That cap is not allowed", "A cap for one run is a whole number from 1 to 10,000. Nothing was started.", "Starting a search", "Change the cap"),
      fr: T("Ce plafond n'est pas autorisé", "Le plafond d'une exécution est un nombre entier de 1 à 10 000. Rien n'a été lancé.", "Le lancement d'une recherche", "Modifier le plafond"),
      ar: T("هذا الحد غير مسموح", "حد التشغيل الواحد عدد صحيح من 1 إلى 10,000. لم يبدأ شيء.", "بدء البحث", "غيّر الحد"),
    },
  },
  // M10b Part D (spec 01-plan "Size estimate", Refusals): the pace only turns records into hours.
  PACE_INVALID: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("Use a whole number of seconds between 5 and 600", "The pace is only used to turn a number of records into hours.", "The screening time shown", "Edit the pace"),
      fr: T("Indiquez un nombre entier de secondes entre 5 et 600", "Le rythme sert seulement à convertir un nombre d'enregistrements en heures.", "Le temps de tri affiché", "Modifier le rythme"),
      ar: T("استخدم عددًا صحيحًا من الثواني بين 5 و600", "تُستخدم الوتيرة فقط لتحويل عدد السجلات إلى ساعات.", "وقت الفرز المعروض", "عدّل الوتيرة"),
    },
  },
  BODY_INVALID: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("The engine could not read this request", "The request's shape is not what the engine expects, for example a number sent as text or a note over 2,000 characters. Nothing was changed. The engine's reason is below.", "This action", "Correct the value named and try again"),
      fr: T("Le moteur n'a pas pu lire cette requête", "La forme de la requête n'est pas celle que le moteur attend, par exemple un nombre envoyé comme texte ou une note de plus de 2 000 caractères. Rien n'a été modifié. La raison du moteur figure ci-dessous.", "Cette action", "Corriger la valeur nommée et réessayer"),
      ar: T("لم يستطع المحرك قراءة هذا الطلب", "شكل الطلب ليس ما يتوقعه المحرك، مثل رقم أُرسل كنص أو ملاحظة تتجاوز 2000 حرف. لم يتغيّر شيء. سبب المحرك أدناه.", "هذا الإجراء", "صحّح القيمة المذكورة وأعد المحاولة"),
    },
  },
  // M10a (spec 03 Refusals; Plan and Harvest of discovery): the unknown names are under Details;
  // the screens supply the button, "Reset to the protocol". Explore's probe has its own card (`inception.probe.`).
  PROVIDER_UNKNOWN: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("The database list was refused", "That database is not one the engine knows. Nothing was started.", "This harvest", "Reset to the protocol"),
      fr: T("La liste des bases a été refusée", "Cette base n'est pas connue du moteur. Rien n'a été lancé.", "Cette collecte", "Revenir au protocole"),
      ar: T("رُفضت قائمة قواعد البيانات", "قاعدة البيانات هذه ليست مما يعرفه المحرك. لم يبدأ شيء.", "هذا الحصاد", "العودة إلى البروتوكول"),
    },
  },
  STAGED_IMPORT_PENDING: {
    role: "unclear",
    action: "discovery-import",
    copy: {
      en: T("Database exports are staged for import", "Accept or remove them before a search run. Nothing was started.", "Starting a search", "Go to Import"),
      fr: T("Des exports de bases attendent l'import", "Acceptez-les ou retirez-les avant une recherche. Rien n'a été lancé.", "Le lancement d'une recherche", "Aller à l'import"),
      ar: T("توجد صادرات قواعد بيانات بانتظار الاستيراد", "اقبلها أو أزلها قبل تشغيل البحث. لم يبدأ شيء.", "بدء البحث", "اذهب إلى الاستيراد"),
    },
  },
  BATCHES_INCOMPLETE: {
    role: "unclear",
    action: "home",
    copy: {
      en: T("Some studies are in no screening batch", "The engine stopped the run; its message is under Details.", "That search", "Go to screening Home"),
      fr: T("Des études ne sont dans aucun lot", "Le moteur a arrêté l'exécution ; son message est dans les détails.", "Cette recherche", "Aller à l'accueil de la sélection"),
      ar: T("بعض الدراسات ليست في أي دفعة فرز", "أوقف المحرك التشغيل؛ رسالته في التفاصيل.", "ذلك البحث", "اذهب إلى صفحة الفرز الرئيسية"),
    },
  },
  PROVIDERS_FAILED: {
    role: "blocked",
    action: "harvest",
    copy: {
      en: T("No database answered", "Every database failed, so no records were kept. Each database's reason is listed with it.", "This search", "Search again"),
      fr: T("Aucune base n'a répondu", "Toutes les bases ont échoué ; aucune notice n'a été gardée. La raison de chaque base est indiquée avec elle.", "Cette recherche", "Chercher à nouveau"),
      ar: T("لم تُجب أي قاعدة بيانات", "فشلت كل قواعد البيانات، فلم يُحفظ أي سجل. سبب كل قاعدة مذكور معها.", "هذا البحث", "ابحث مجددًا"),
    },
  },
  DISCOVERY_FAILED: {
    role: "blocked",
    action: "harvest",
    copy: {
      en: T("The search failed", "Something other than a database stopped it. The engine's text is under Details.", "This search", "Search again"),
      fr: T("La recherche a échoué", "Autre chose qu'une base l'a arrêtée. Le texte du moteur est dans les détails.", "Cette recherche", "Chercher à nouveau"),
      ar: T("فشل البحث", "أوقفه شيء غير قواعد البيانات. نص المحرك في التفاصيل.", "هذا البحث", "ابحث مجددًا"),
    },
  },
  ACCEPT_CORPUS_REFUSED: {
    role: "blocked",
    action: "retry",
    copy: {
      en: T("The engine refused to freeze the corpus", "Its own message is under Details. Nothing was frozen.", "Accepting", "Try again"),
      fr: T("Le moteur a refusé de figer le corpus", "Son message est dans les détails. Rien n'a été figé.", "L'acceptation", "Réessayer"),
      ar: T("رفض المحرك تجميد المجموعة", "رسالته في التفاصيل. لم يُجمَّد شيء.", "القبول", "إعادة المحاولة"),
    },
  },
  // Inception recon (specs 02 Explore and 03 Direction, M4d). Three codes that
  // discovery or screening also use carry their inception meaning under the
  // `inception.` prefix (`inceptionStateKey`).
  // M10b Part B (`docs/ux/shared/final/01-proposals.md`): a decision on a
  // proposal. The card itself is the next step (it re-reads, or offers Edit).
  PROPOSAL_NOT_FOUND: {
    role: "unclear",
    action: "none",
    copy: {
      en: T("That suggestion is no longer there", "The engine has no suggestion with this id on this draft. Nothing was changed.", "This suggestion", "Read the suggestions again"),
      fr: T("Cette suggestion n'existe plus", "Le moteur n'a aucune suggestion avec cet identifiant sur ce brouillon. Rien n'a été changé.", "Cette suggestion", "Relire les suggestions"),
      ar: T("لم يعد ذلك الاقتراح موجودًا", "لا يملك المحرك اقتراحًا بهذا المعرّف في هذه المسودة. لم يتغير شيء.", "هذا الاقتراح", "اقرأ الاقتراحات مجددًا"),
    },
  },
  PROPOSAL_STALE: {
    role: "unclear",
    action: "none",
    copy: {
      en: T("This field changed after the suggestion was made", "Applying it now could overwrite your own words, so nothing was applied.", "This suggestion", "Dismiss it; the check offers a new one if it still holds"),
      fr: T("Ce champ a changé après la suggestion", "L'appliquer maintenant pourrait écraser vos propres mots ; rien n'a été appliqué.", "Cette suggestion", "L'écarter ; la vérification en propose une nouvelle si elle tient toujours"),
      ar: T("تغيّر هذا الحقل بعد تقديم الاقتراح", "تطبيقه الآن قد يكتب فوق كلماتك، لذا لم يُطبَّق شيء.", "هذا الاقتراح", "تجاهله؛ يقدّم الفحص اقتراحًا جديدًا إن ظل قائمًا"),
    },
  },
  PROPOSAL_NOT_OPEN: {
    role: "unclear",
    action: "none",
    copy: {
      en: T("This suggestion is already decided", "It was applied or rejected already, or its value is already in the field. Nothing was changed.", "This suggestion", "Read its state again"),
      fr: T("Cette suggestion est déjà décidée", "Elle a déjà été appliquée ou rejetée, ou sa valeur est déjà dans le champ. Rien n'a été changé.", "Cette suggestion", "Relire son état"),
      ar: T("تقرّر في هذا الاقتراح مسبقًا", "طُبّق أو رُفض من قبل، أو قيمته موجودة في الحقل. لم يتغير شيء.", "هذا الاقتراح", "اقرأ حالته مجددًا"),
    },
  },
  PROPOSAL_TARGET_UNSUPPORTED: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("The engine cannot apply a suggestion to this field", "The field is not one of the draft's answers, or the change does not fit it. Nothing was changed.", "This suggestion", "Reject it, or change the field yourself"),
      fr: T("Le moteur ne peut pas appliquer de suggestion à ce champ", "Ce champ ne fait pas partie des réponses du brouillon, ou le changement ne lui convient pas. Rien n'a été changé.", "Cette suggestion", "La rejeter, ou modifier le champ vous-même"),
      ar: T("لا يستطيع المحرك تطبيق اقتراح على هذا الحقل", "الحقل ليس من إجابات المسودة، أو التغيير لا يناسبه. لم يتغير شيء.", "هذا الاقتراح", "ارفضه، أو غيّر الحقل بنفسك"),
    },
  },
  PROPOSAL_SOURCE_REFUSED: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("This version does not take suggestions from that source", "Only the fixed checks and an imported protocol may suggest changes here. Nothing was recorded.", "This suggestion", "Reject it, or change the field yourself"),
      fr: T("Cette version n'accepte pas de suggestions de cette source", "Seules les vérifications fixes et un protocole importé peuvent suggérer des changements ici. Rien n'a été enregistré.", "Cette suggestion", "La rejeter, ou modifier le champ vous-même"),
      ar: T("لا يقبل هذا الإصدار اقتراحات من ذلك المصدر", "وحدها الفحوص الثابتة والبروتوكول المستورد تستطيع اقتراح تغييرات هنا. لم يُسجَّل شيء.", "هذا الاقتراح", "ارفضه، أو غيّر الحقل بنفسك"),
    },
  },
  // M10b Part B (`docs/ux/shared/final/02-checks.md`): dismissing and restoring a
  // check, on the inception and the discovery screens alike.
  CHECK_NOT_FOUND: {
    role: "unclear",
    action: "none",
    copy: {
      en: T("That check is no longer there", "The data changed and the engine no longer finds this check. Nothing was dismissed.", "This check", "Read the checks again"),
      fr: T("Cette vérification n'existe plus", "Les données ont changé et le moteur ne trouve plus cette vérification. Rien n'a été écarté.", "Cette vérification", "Relire les vérifications"),
      ar: T("لم يعد ذلك الفحص موجودًا", "تغيّرت البيانات ولم يعد المحرك يجد هذا الفحص. لم يُتجاهل شيء.", "هذا الفحص", "اقرأ الفحوص مجددًا"),
    },
  },
  CHECK_NOT_DISMISSIBLE: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("This check cannot be dismissed", "It is a refusal the engine will repeat, or it is answered by the confirmation in the gate. Nothing was dismissed.", "This check", "Fix what it names"),
      fr: T("Cette vérification ne peut pas être écartée", "C'est un refus que le moteur répétera, ou la confirmation de la validation y répond. Rien n'a été écarté.", "Cette vérification", "Corriger ce qu'elle nomme"),
      ar: T("لا يمكن تجاهل هذا الفحص", "إنه رفض سيكرره المحرك، أو يُجاب عنه بالتأكيد في البوابة. لم يُتجاهل شيء.", "هذا الفحص", "أصلح ما يذكره"),
    },
  },
  CHECK_REASON_REQUIRED: {
    role: "unclear",
    action: "none",
    copy: {
      en: T("A warning is dismissed with a reason", "The reason is empty, or longer than the draft's text limit. Nothing was dismissed.", "This check", "Write a short reason"),
      fr: T("Un avertissement s'écarte avec une raison", "La raison est vide, ou plus longue que la limite de texte du brouillon. Rien n'a été écarté.", "Cette vérification", "Écrire une courte raison"),
      ar: T("يُتجاهل التحذير مع سبب", "السبب فارغ، أو أطول من حد النص في المسودة. لم يُتجاهل شيء.", "هذا الفحص", "اكتب سببًا قصيرًا"),
    },
  },
  CHECK_CHANGED: {
    role: "unclear",
    action: "none",
    copy: {
      en: T("The data changed since the page read this check", "Its numbers are not the ones you saw, so nothing was dismissed.", "This check", "Read it again"),
      fr: T("Les données ont changé depuis la lecture de cette vérification", "Ses nombres ne sont plus ceux que vous avez vus ; rien n'a été écarté.", "Cette vérification", "La relire"),
      ar: T("تغيّرت البيانات منذ قرأت الصفحة هذا الفحص", "أرقامه ليست التي رأيتها، لذا لم يُتجاهل شيء.", "هذا الفحص", "اقرأه مجددًا"),
    },
  },
  CHECK_NOT_DISMISSED: {
    role: "unclear",
    action: "none",
    copy: {
      en: T("This check is not dismissed", "It is open already, so there is nothing to restore.", "This check", "Read the checks again"),
      fr: T("Cette vérification n'est pas écartée", "Elle est déjà ouverte ; il n'y a rien à rétablir.", "Cette vérification", "Relire les vérifications"),
      ar: T("هذا الفحص غير متجاهَل", "إنه مفتوح أصلًا، فلا شيء لاستعادته.", "هذا الفحص", "اقرأ الفحوص مجددًا"),
    },
  },
  // M10b (spec 09): starting a draft from an earlier protocol. The screen's own
  // buttons ("Choose a different source", "Read it again") are the next step.
  IMPORT_SOURCE_NOT_FOUND: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("That protocol is not there", "The workspace folder or its protocol.json is not on this computer any more.", "Starting from it", "Choose another source"),
      fr: T("Ce protocole n'est pas là", "Le dossier de l'espace ou son protocol.json n'est plus sur cet ordinateur.", "Le départ depuis celui-ci", "Choisir une autre source"),
      ar: T("ذلك البروتوكول غير موجود", "لم يعد مجلد مساحة العمل أو ملف protocol.json الخاص بها على هذا الحاسوب.", "البدء منه", "اختر مصدرًا آخر"),
    },
  },
  IMPORT_SOURCE_UNREADABLE: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("That file cannot be read", "It is not text in UTF-8, or not JSON, or not a JSON object. Details says which.", "Starting from it", "Choose another file"),
      fr: T("Ce fichier ne peut pas être lu", "Ce n'est pas du texte UTF-8, ou pas du JSON, ou pas un objet JSON. Les détails disent lequel.", "Le départ depuis celui-ci", "Choisir un autre fichier"),
      ar: T("لا يمكن قراءة ذلك الملف", "ليس نصًا بترميز UTF-8، أو ليس JSON، أو ليس كائن JSON. توضح التفاصيل أيها.", "البدء منه", "اختر ملفًا آخر"),
    },
  },
  IMPORT_SOURCE_TOO_LARGE: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("That file is too large for a protocol", "A protocol file is a few kilobytes. This one is over 1 MB.", "Starting from it", "Choose another file"),
      fr: T("Ce fichier est trop grand pour un protocole", "Un fichier de protocole fait quelques kilo-octets. Celui-ci dépasse 1 Mo.", "Le départ depuis celui-ci", "Choisir un autre fichier"),
      ar: T("ذلك الملف أكبر من أن يكون بروتوكولًا", "ملف البروتوكول بضعة كيلوبايتات. هذا الملف أكبر من 1 ميغابايت.", "البدء منه", "اختر ملفًا آخر"),
    },
  },
  IMPORT_NOT_A_PROTOCOL: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("That is not a protocol", "It is JSON, but it has no research questions, criteria and search strategy. Details lists what is missing.", "Starting from it", "Choose protocol.json or intent.json"),
      fr: T("Ce n'est pas un protocole", "C'est du JSON, mais il n'a ni questions de recherche, ni critères, ni stratégie de recherche. Les détails listent ce qui manque.", "Le départ depuis celui-ci", "Choisir protocol.json ou intent.json"),
      ar: T("هذا ليس بروتوكولًا", "إنه JSON، لكنه بلا أسئلة بحث ولا معايير ولا استراتيجية بحث. تسرد التفاصيل ما ينقص.", "البدء منه", "اختر protocol.json أو intent.json"),
    },
  },
  IMPORT_PROTOCOL_VERSION_UNSUPPORTED: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("This protocol is from a version this app does not read", "Its $schema is not the one this app reads. Nothing was guessed. Details shows both.", "Starting from it", "Choose another source"),
      fr: T("Ce protocole vient d'une version que l'application ne lit pas", "Son $schema n'est pas celui que l'application lit. Rien n'a été deviné. Les détails montrent les deux.", "Le départ depuis celui-ci", "Choisir une autre source"),
      ar: T("هذا البروتوكول من إصدار لا يقرؤه التطبيق", "قيمة $schema فيه ليست التي يقرؤها التطبيق. لم يُخمَّن شيء. تعرض التفاصيل القيمتين.", "البدء منه", "اختر مصدرًا آخر"),
    },
  },
  IMPORT_SOURCE_CHANGED: {
    role: "unclear",
    action: "none",
    copy: {
      en: T("That protocol changed while you were looking", "Its fingerprint is not the one the report showed. No draft was created.", "Creating the draft", "Read it again"),
      fr: T("Ce protocole a changé pendant que vous le lisiez", "Son empreinte n'est pas celle que le rapport montrait. Aucun brouillon n'a été créé.", "La création du brouillon", "Relire"),
      ar: T("تغيّر ذلك البروتوكول أثناء اطلاعك عليه", "بصمته ليست التي عرضها التقرير. لم تُنشأ أي مسودة.", "إنشاء المسودة", "اقرأه مجددًا"),
    },
  },
  "inception.PROTOCOL_INVALID": {
    role: "blocked",
    action: "none",
    copy: {
      en: T("This protocol does not pass the protocol check", "It looks like a protocol, but a field has the wrong type or value. Details lists them.", "Starting from it", "Choose another source"),
      fr: T("Ce protocole ne passe pas la vérification", "Il ressemble à un protocole, mais un champ a le mauvais type ou la mauvaise valeur. Les détails les listent.", "Le départ depuis celui-ci", "Choisir une autre source"),
      ar: T("لا يجتاز هذا البروتوكول فحص البروتوكول", "يبدو بروتوكولًا، لكن أحد الحقول بنوع أو قيمة خاطئة. تسردها التفاصيل.", "البدء منه", "اختر مصدرًا آخر"),
    },
  },
  "inception.STALE_BINDING": {
    role: "unclear",
    action: "inception-step",
    copy: {
      en: T("The direction was chosen on a pool or a scope that no longer matches", "The search ran again, or the scope changed, after you chose it. Nothing was written.", "The preview and creating the workspace", "Choose the direction again"),
      fr: T("La direction a été choisie sur un corpus ou une portée qui ne correspondent plus", "La recherche a été relancée, ou la portée a changé, après votre choix. Rien n'a été écrit.", "L'aperçu et la création de l'espace", "Choisir de nouveau la direction"),
      ar: T("اختير الاتجاه على مجموعة أوراق أو نطاق لم يعودا مطابقين", "أُعيد البحث، أو تغيّر النطاق، بعد اختيارك له. لم يُكتب شيء.", "المعاينة وإنشاء مساحة العمل", "اختر الاتجاه من جديد"),
    },
  },
  "inception.MAILTO_NOT_SET": {
    role: "blocked",
    action: "reload",
    command: "SCHOLAR_MAILTO=<your email>",
    copy: {
      en: T("This console has no contact email for the literature databases", "A search needs one, and no request was sent. There is no setting for it in the app yet: set SCHOLAR_MAILTO in the environment or the .env of the console and start the console again.", "New searches (a pool already on screen still works)", "Reload the page"),
      fr: T("Cette console n'a pas d'adresse de contact pour les bases bibliographiques", "Une recherche en demande une, et aucune requête n'a été envoyée. L'application n'a pas encore de réglage pour cela : définissez SCHOLAR_MAILTO dans l'environnement ou le .env de la console, puis redémarrez la console.", "Les nouvelles recherches (un corpus déjà affiché reste utilisable)", "Recharger la page"),
      ar: T("ليس لوحدة التحكم هذه بريد للتواصل مع قواعد البيانات العلمية", "يحتاج البحث إلى بريد، ولم يُرسل أي طلب. لا يوجد إعداد لذلك في التطبيق بعد: عيّن SCHOLAR_MAILTO في بيئة وحدة التحكم أو ملف ‎.env‎ الخاص بها، ثم أعد تشغيلها.", "عمليات البحث الجديدة (تبقى مجموعة الأوراق المعروضة صالحة)", "أعد تحميل الصفحة"),
    },
  },
  "inception.PROVIDERS_FAILED": {
    role: "blocked",
    action: "explore-search",
    copy: {
      en: T("Every database failed to answer", "There is no pool. Nothing was cached; try again later. The table names each failure.", "This search", "Search again"),
      fr: T("Aucune base n'a répondu", "Il n'y a pas de corpus. Rien n'a été mis en cache ; réessayez plus tard. Le tableau indique chaque échec.", "Cette recherche", "Chercher à nouveau"),
      ar: T("لم تُجب أي قاعدة بيانات", "لا توجد مجموعة أوراق. لم يُخزَّن شيء مؤقتًا؛ حاول لاحقًا. يذكر الجدول كل إخفاق.", "هذا البحث", "ابحث مجددًا"),
    },
  },
  // M10a (spec 02 Refusals): the probe's database list and query, for Explore's probe refusals only
  // (`probeStateKey`); every other inception screen keeps the generic card. Explore supplies the button.
  "inception.probe.PROVIDER_UNKNOWN": {
    role: "blocked",
    action: "none",
    copy: {
      en: T("That database list cannot be searched", "The engine accepts a non-empty list of OpenAlex, Semantic Scholar, Crossref and arXiv, each once. Nothing was sent.", "This search", "Reset the databases"),
      fr: T("Cette liste de bases ne peut pas être interrogée", "Le moteur accepte une liste non vide d'OpenAlex, Semantic Scholar, Crossref et arXiv, chacune une seule fois. Rien n'a été envoyé.", "Cette recherche", "Réinitialiser les bases"),
      ar: T("لا يمكن البحث في قائمة قواعد البيانات هذه", "يقبل المحرك قائمة غير فارغة من OpenAlex وSemantic Scholar وCrossref وarXiv، كل منها مرة واحدة. لم يُرسل شيء.", "هذا البحث", "أعد ضبط قواعد البيانات"),
    },
  },
  "inception.probe.BODY_INVALID": {
    role: "blocked",
    action: "none",
    copy: {
      en: T("That search request was not valid", "The query must be 1 to 2000 characters and cannot be sent with a narrower search. Nothing was sent.", "This search", "Edit the query"),
      fr: T("Cette requête de recherche n'était pas valide", "La requête doit compter de 1 à 2000 caractères et ne peut pas être envoyée avec une recherche plus étroite. Rien n'a été envoyé.", "Cette recherche", "Modifier la requête"),
      ar: T("طلب البحث هذا غير صالح", "يجب أن يتراوح الاستعلام بين 1 و2000 حرف، ولا يمكن إرساله مع بحث أضيق. لم يُرسل شيء.", "هذا البحث", "عدّل الاستعلام"),
    },
  },
  RECON_JOB_ACTIVE: {
    role: "unclear",
    action: "retry",
    copy: {
      en: T("A search for this draft is already running", "Only one runs at a time.", "Starting another search", "Watch the running search"),
      fr: T("Une recherche est déjà en cours pour ce brouillon", "Une seule à la fois.", "Le lancement d'une autre recherche", "Suivre la recherche en cours"),
      ar: T("يجري بحث لهذه المسودة بالفعل", "لا يجري إلا بحث واحد في كل مرة.", "بدء بحث آخر", "تابع البحث الجاري"),
    },
  },
  POOL_EMPTY: {
    role: "blocked",
    action: "inception-step",
    copy: {
      en: T("The search found no papers", "Nothing was cached. Widen the years or rephrase the question. The table shows what each database answered.", "This search", "Change scope"),
      fr: T("La recherche n'a trouvé aucun article", "Rien n'a été mis en cache. Élargissez les années ou reformulez la question. Le tableau montre la réponse de chaque base.", "Cette recherche", "Modifier la portée"),
      ar: T("لم يجد البحث أي ورقة", "لم يُخزَّن شيء مؤقتًا. وسّع السنوات أو أعد صياغة السؤال. يبيّن الجدول ما أجابت به كل قاعدة.", "هذا البحث", "غيّر النطاق"),
    },
  },
  RECON_FAILED: {
    role: "blocked",
    action: "explore-search",
    copy: {
      en: T("The search stopped on an unexpected error", "The engine's report is under Details. Nothing was cached.", "This search", "Search again"),
      fr: T("La recherche s'est arrêtée sur une erreur inattendue", "Le rapport du moteur est dans les détails. Rien n'a été mis en cache.", "Cette recherche", "Chercher à nouveau"),
      ar: T("توقف البحث بسبب خطأ غير متوقع", "تقرير المحرك في التفاصيل. لم يُخزَّن شيء مؤقتًا.", "هذا البحث", "ابحث مجددًا"),
    },
  },
  RECON_NO_POOL: {
    role: "unclear",
    action: "inception-step",
    copy: {
      en: T("There is no pool yet", "A search has to succeed first.", "Reading the pool", "Search the literature"),
      fr: T("Il n'y a pas encore de corpus", "Une recherche doit d'abord réussir.", "La lecture du corpus", "Chercher dans la littérature"),
      ar: T("لا توجد مجموعة أوراق بعد", "يجب أن ينجح بحث أولًا.", "قراءة مجموعة الأوراق", "ابحث في الأدبيات"),
    },
  },
  RECON_SESSION_NOT_FOUND: {
    role: "unclear",
    action: "inception-step",
    copy: {
      en: T("This draft has not searched yet", "Its pool can be read once a search has succeeded.", "Reading the pool", "Search the literature"),
      fr: T("Ce brouillon n'a pas encore cherché", "Son corpus se lit une fois qu'une recherche a réussi.", "La lecture du corpus", "Chercher dans la littérature"),
      ar: T("لم تُجرِ هذه المسودة أي بحث بعد", "تُقرأ مجموعة أوراقها بعد أن ينجح بحث.", "قراءة مجموعة الأوراق", "ابحث في الأدبيات"),
    },
  },
  RECON_SESSION_INVALID: {
    role: "blocked",
    action: "inception",
    copy: {
      en: T("That is not a search session id", "The draft link may be cut short.", "This page only", "Go to your drafts"),
      fr: T("Ce n'est pas un identifiant de session de recherche", "Le lien du brouillon est peut-être tronqué.", "Cette page seulement", "Aller à vos brouillons"),
      ar: T("هذا ليس معرّف جلسة بحث", "ربما اقتُطع رابط المسودة.", "هذه الصفحة فقط", "اذهب إلى مسوداتك"),
    },
  },
  RECON_JOB_NOT_FOUND: {
    role: "unclear",
    action: "retry",
    copy: {
      en: T("The search can no longer be followed", "The console may have restarted. The pool, if one arrived, is below.", "This page only", "Reload the pool"),
      fr: T("La recherche ne peut plus être suivie", "La console a peut-être redémarré. Le corpus, s'il est arrivé, est ci-dessous.", "Cette page seulement", "Recharger le corpus"),
      ar: T("لم يعد ممكنًا متابعة البحث", "ربما أُعيد تشغيل وحدة التحكم. مجموعة الأوراق، إن وصلت، أدناه.", "هذه الصفحة فقط", "أعد تحميل مجموعة الأوراق"),
    },
  },
  POOL_TOO_SMALL: {
    role: "unclear",
    action: "none",
    copy: {
      en: T("The pool is under the floor for a direction", "Directions from so few papers are often fragments. Nothing was bound.", "Choosing a direction", "Accept a small pool and choose again"),
      fr: T("Le corpus est sous le seuil d'une direction", "Les directions tirées de si peu d'articles sont souvent des fragments. Rien n'a été lié.", "Le choix d'une direction", "Accepter un petit corpus et choisir de nouveau"),
      ar: T("مجموعة الأوراق دون الحد الأدنى لاتجاه", "الاتجاهات المستخلصة من أوراق قليلة كهذه كثيرًا ما تكون أجزاء. لم يُربط شيء.", "اختيار اتجاه", "اقبل مجموعة صغيرة واختر من جديد"),
    },
  },
  NO_DIRECTION: {
    role: "blocked",
    action: "none",
    copy: {
      en: T("Choose one direction, write your own, or go on without one", "Exactly one is needed.", "Choosing a direction", "Choose a direction"),
      fr: T("Choisissez une direction, écrivez la vôtre, ou continuez sans", "Il en faut exactement une.", "Le choix d'une direction", "Choisir une direction"),
      ar: T("اختر اتجاهًا واحدًا، أو اكتب اتجاهك، أو تابع من دون اتجاه", "المطلوب واحد بالضبط.", "اختيار اتجاه", "اختر اتجاهًا"),
    },
  },
  DIRECTION_UNKNOWN: {
    role: "unclear",
    action: "retry",
    copy: {
      en: T("That is not a direction of the current pool", "The pool may have changed since you opened this page. The current directions are listed.", "Choosing a direction, or a narrower search", "Reload the directions"),
      fr: T("Ce n'est pas une direction du corpus actuel", "Le corpus a peut-être changé depuis l'ouverture de cette page. Les directions actuelles sont listées.", "Le choix d'une direction, ou une recherche plus étroite", "Recharger les directions"),
      ar: T("هذا ليس اتجاهًا من مجموعة الأوراق الحالية", "ربما تغيّرت المجموعة منذ فتحت هذه الصفحة. الاتجاهات الحالية مذكورة.", "اختيار اتجاه، أو بحث أضيق", "أعد تحميل الاتجاهات"),
    },
  },
  NARROW_BUDGET_SPENT: {
    role: "unclear",
    action: "none",
    copy: {
      en: T("The one narrower search of this draft is used", "It cannot be run again.", "Narrower search", "Back to the directions"),
      fr: T("La recherche plus étroite de ce brouillon est utilisée", "Elle ne peut pas être relancée.", "La recherche plus étroite", "Retour aux directions"),
      ar: T("استُخدم البحث الأضيق الوحيد لهذه المسودة", "لا يمكن إجراؤه مرة أخرى.", "البحث الأضيق", "العودة إلى الاتجاهات"),
    },
  },
  // M10b Part C (02-explore "Sample curation"): leaving papers out of the Explore sample.
  // The screen's own "Try again" re-reads the papers and the sample (action `retry`).
  PAPER_UNKNOWN: {
    role: "unclear",
    action: "retry",
    copy: {
      en: T("That paper is not in this sample", "The sample may have changed since you opened the page. Nothing was changed.", "Leaving a paper out", "Reload the papers"),
      fr: T("Cet article n'est pas dans cet échantillon", "L'échantillon a peut-être changé depuis l'ouverture de la page. Rien n'a été modifié.", "L'écartement d'un article", "Recharger les articles"),
      ar: T("هذه الورقة ليست في هذه العيّنة", "ربما تغيّرت العيّنة منذ فتحت الصفحة. لم يتغيّر شيء.", "استبعاد ورقة", "أعد تحميل الأوراق"),
    },
  },
  // The limit (`details.limit`) is printed by the screen under the card, from the engine's details.
  SAMPLE_EXCLUSIONS_FULL: {
    role: "unclear",
    action: "inception-step",
    copy: {
      en: T("You have left out as many papers as this draft can record", "Put some back, or search again with a narrower question.", "Leaving papers out", "Change scope"),
      fr: T("Vous avez écarté autant d'articles que ce brouillon peut en enregistrer", "Remettez-en, ou relancez une recherche avec une question plus étroite.", "L'écartement d'articles", "Modifier la portée"),
      ar: T("استبعدت أكبر عدد من الأوراق يمكن لهذه المسودة تسجيله", "أعد بعضها، أو ابحث مجددًا بسؤال أضيق.", "استبعاد الأوراق", "غيّر النطاق"),
    },
  },
  TERM_EMPTY: {
    role: "unclear",
    action: "none",
    copy: {
      en: T("Type a phrase to check", "An empty phrase cannot be looked up. Nothing was checked.", "The phrase check", "Write your direction first"),
      fr: T("Saisissez une expression à vérifier", "Une expression vide ne peut pas être cherchée. Rien n'a été vérifié.", "La vérification de l'expression", "Écrivez d'abord votre direction"),
      ar: T("اكتب عبارة للتحقق منها", "لا يمكن البحث عن عبارة فارغة. لم يُتحقق من شيء.", "التحقق من العبارة", "اكتب اتجاهك أولًا"),
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
  command?: string;
}

const UNKNOWN: Record<Locale, { title: string; body: string }> = {
  en: { title: "Refused", body: "The engine refused this with the code below." },
  fr: { title: "Refusé", body: "Le moteur a refusé avec le code ci-dessous." },
  ar: { title: "مرفوض", body: "رفض المحرك ذلك بالرمز أدناه." },
};

/**
 * The inception screens (M4d) share three codes with discovery and screening
 * whose meaning differs there (`STALE_BINDING`, `MAILTO_NOT_SET`,
 * `PROVIDERS_FAILED`); their inception cards are registered under this prefix.
 */
export const INCEPTION_SCOPE = "inception.";

/** The card key for a code shown on an inception screen: the scoped one when it exists. */
export function inceptionStateKey(code: string): string {
  return STATES[INCEPTION_SCOPE + code] ? INCEPTION_SCOPE + code : code;
}

/**
 * Explore's probe refusals (M10a): `PROVIDER_UNKNOWN` and `BODY_INVALID` of
 * `POST .../recon/probe` name the database list and the query. Their cards sit
 * under `inception.probe.`, which `inceptionStateKey` never resolves to, so a
 * `BODY_INVALID` on any other inception screen keeps the generic card.
 */
export const PROBE_SCOPE = "inception.probe.";

/** The card key for a refusal of Explore's probe start: the probe card when one exists, else the inception key. */
export function probeStateKey(code: string): string {
  return STATES[PROBE_SCOPE + code] ? PROBE_SCOPE + code : inceptionStateKey(code);
}

/** The card for a code; an unknown code renders as itself, never as another card. */
export function stateCopy(locale: Locale, code: string): StateCopy {
  const entry = STATES[code] ?? (code === "CONSOLE_UNREACHABLE" || code === "CONSOLE_TIMEOUT" ? STATES.ENGINE_UNREACHABLE : undefined);
  if (!entry) {
    return { code, known: false, role: "blocked", action: "none", title: UNKNOWN[locale].title, body: UNKNOWN[locale].body, affects: "", actionLabel: "" };
  }
  const c = entry.copy[locale];
  return { code, known: true, role: entry.role, action: entry.action, title: c.title, body: c.body, affects: c.affects, actionLabel: c.action, command: entry.command };
}

export const AFFECTS_LABEL: Record<Locale, string> = { en: "Affects:", fr: "Concerne :", ar: "يؤثر في:" };
