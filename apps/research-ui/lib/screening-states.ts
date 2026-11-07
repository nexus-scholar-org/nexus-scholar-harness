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

export type StateAction = "import" | "prepare" | "proposals" | "triage" | "publish" | "home" | "retry" | "reload" | "terminal" | "none";

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
  VERIFIED_EXISTS: {
    role: "blocked",
    action: "prepare",
    copy: {
      en: T("This workspace already has a corpus", "Its records came from the app's own search (literature/verified.json). Database exports would replace them, so none can be added here.", "Importing database exports", "Go to Prepare"),
      fr: T("Cet espace a déjà un corpus", "Ses notices viennent de la recherche de l'application (literature/verified.json). Des exports de bases les remplaceraient ; aucun ne peut donc être ajouté ici.", "L'import d'exports de bases", "Aller à Préparer"),
      ar: T("لهذه المساحة مجموعة بالفعل", "جاءت سجلاتها من بحث التطبيق نفسه (literature/verified.json). ستحل محلها صادرات قواعد البيانات، لذا لا يمكن إضافة أي منها هنا.", "استيراد صادرات قواعد البيانات", "الذهاب إلى التحضير"),
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
