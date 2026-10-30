# Berber 0.6.0 implementation ledger

Plan: approved conversation plan, 26 native unit voice families, verified 0.5.1 base.

## Constraints and rulings
- Base SGA SHA256 acbcd6501a1e8ebea2c7dae8701641625c96c078e3a4d33e9c2968111732717b. Preserve 0.5.1 and all unrelated source/art/gameplay.
- Ruling: isolated release-owned authoring/output directories rather than a HEAD-only Git worktree: current production inputs are substantially untracked; archive 0.5.1 is authoritative. Do not alter existing root assets or other releases.
- Historical mix; Arabic fallback permitted for failed/unverifiable Amazigh/Tuareg. Balanced 3 frequent/2 rare selectable takes, all supported ages/deliveries. Efforts must be nonverbal.
- Credentials only process memory; no secret in scripts, argv, logs, reports or packages. Existing prepaid credits only; no overage or subscription mutations.
- Native playback is a separate gate. Do not terminate an existing game or interrupt unsaved Blender work.

## Task ledger
1. Base/inventory/profile feasibility: complete, 26 private profiles; 20,939 native media paths. See profile implementation report.
2. Historical scripts and characters: complete authored 5,339 recording jobs, 26 distinct Arabic professional actors. Unsupported Amazigh/Tuareg falls back to Arabic with explicit documentation.
3. Account/quota and generation pilots: 112 character pilot jobs all acoustic accepted; 3 timestamp-batch cuts accepted. Fourteen supplementary ASR checks complete (Tuareg/Imam exact command match, gunner vowel marks improved after ambiguity). API account read lacks permission; human explicitly confirmed $100 credit for key. Ruling: this is the authorized prepaid budget snapshot, not live API quota proof. No subscription changes or topups permitted.
4. Batch generation/encoding: ready for full generation after retry-orphan fix. 96,297 characters, current official list estimate $7.7038, conservative $0.30/1k with 20% retry estimate $34.6669 within $100 cap. Medium Wwise conversion selected provisionally from independently decoded Low/Medium/High comparison; listening/native acceptance pending.
5. Speech bindings: 84 RGD payloads verified with full semantic undo; Masmuda full-context archer donor fixes Age II, King age II remap corrected. Native review found no confirmed blocker. Full archive composition pending.
6. Installer: standalone PS5.1+ script with Validate/Install/Verify/Uninstall; 13 tests pass, 1 junction-creation fixture skipped on exFAT. No game files installed or game process changed. Package/cleanup pending.

## Current known limits and corrections
- Current stock profiles lack separate Age I forms for fishing/transport/King, and Age II fire ship; exact context gaps preserved, no unsafe SPD record growth. King I shares II, fire II shares III; document rather than claim distinct early-age playback.
- API rejects concurrent requests for the same actor with HTTP409 already_running. Serialize by actor; run up to4 different actors. Explicit409 refusals retried with fresh conservative reservations, unknown outcomes never blindly retried.
- Generation reviewer found retry-reservation interruption hole; regression test failed before fix, passed after guarding exact retry attempt reservation.
- 0.5.1 source assets unchanged. Output directory is E: junction to F:; installer validation must use physical resolved package root, or extracted companion outside junctions.

## Interface ownership
- Profile specialist: research/berber060/profiles.py, test_profiles.py, inventory.py and output inventory/profiles only.
- Script researcher: research/berber060/scripts.py, history.md and source script manifest only.
- Coordinator: common/API/generation/encoding/bindings/release/installer, final acceptance and cleanup.
- All specialists: no paid API calls, no game/Blender changes, no source-root edits.

## Resumption and integration update
- Shared account credential was reenabled by the human; read-only authentication passed. Explicit401 refusals received fresh request identities; unknown in-flight outcomes remain held, never blindly retried. Authentication now stops the entire queue.
- Candidate composed from exact051: SHA25641d4f2255610c723c66c816ae51ea9247c368c5c8d262120eb335b90c8a92948. All unrelated members/art identical;85 admitted speech payloads incl metadata.
- Last completed offline suite:56tests passed,1filesystem-specificskip. Installer separately passes14tests+1skip on actualPowerShell5.1 and7.
- Queue paused on exFAT/Windows atomic receipt replacement PermissionError; source-preserving recovery and bounded write retries in progress. Last snapshot1075/5339 accepted, generation stopped; no complete delivery yet.
- Final package helper validates full20939 nativealiases,26profiles and content-addressed blobs; incomplete sources fail closed. Finaldelivery+cleanup helpers being prepared.

## Network recovery checkpoint (2026-10-16 UTC10:26 onward)
- Second bulk process25636/session23405 completed, no coordinator active. Results:2014accepted_acoustic,82review_required,2813rejected_or_unknown,419failed_or_unknown,3started+8started_batch.
- Main outage root cause:2717receipts contain getaddrinfo11001 (2304batchmembers+413singles). DNS and read-only authenticatedGET then recovered. No game/Blender/config changes. Legacy transport reservations remain conservatively counted because oldredirecttrace is unavailable; reviewed replacements get fresh epochs.
- Partial offline recovery applied:266safeclips from56batches; allreceipt/audio/master/alignment hashes independently reverified; budgethash unchanged. Default strictsplit validation retained; unsafe neighboring clips remain rejected.
- rootmanual_outcomes.py explicitly prepared11new performances after unrecoverable interrupted originals/historylookup; originalunknownreservations retained. repair.py then prepared280qualityretakes. jobs.py has pendingvowel-marked simplifiedarcherselection textoverride fromuncertainlocalASRflag; compileafterDNShelper runs.
- LocalWhisper52spotchecks (26characters×command+effort), cachedsmallmodelSHAverified, no network/modeldownload;0literalEnglishdirectionwordflags; oneuncertainarchercommandmarkedfornewclearerretake. Allresults supplementary, no nativepronunciationapproval implied.
- Loudnessstock8samples:commandsmedian -21.48LUFS vsnew -15.075; final gain-onlytarget -21.5 with eventmatchedefforts/RMSproxyshortclips. normalize_all.py+9tests ready, productionnormalization NOTYETRUN.
- Prepared final_audio.py fullWwiseMedium+independentdecodeeveryWEM; package_audio.py; delivery.py; cleanup.py. NofinalZIPyet, nocleanupyet, noactualgameinstallation/audibletests.
- Next: generation_review finishes DNS/unknowntransportstop + reset_dns_failures.py; rootexecute --include-reviewed-legacy aftertests, jobs.py, then resumebulk4actorworkers. No other budgetwriter. Afterpass: offlinepartial recovery, boundedqualityrepairs, exactvariationcoverage, normalization, encode/decode, package/ZIPverify, safeAGENTS/STORAGEcleanup/hashrecheck.

## Active queue checkpoint (UTC10:44)
- reset_dns_failures.py --include-reviewed-legacy successfully requeued2717 legacyDNS jobs; releasedUSD0; alloriginaluncertain reservations retained. Proofdns-reconciliation/20261016T103353815060Z.json. Read-onlyauth/networkprobe passed.
- Recompiledcurrentplan5339jobs/20939aliases,96332characters includingvowel-markedarcherrevision. Current paidcoordinator execsession98505 (fouractors), resumed after137tests passed+2filesystem skips. Newauthentication/quota/DNS/unknowntransport stopgates active; peractorbatchqualityfallback active.
- Actualgenerationhas reachedsiege. Fullrecordingcompletion/pendingqualityretakes stilloutstanding. Budgetconservative reservations ~USD43 includingoldDNSuncertainty, cap100 unchanged; invoicebalance unavailable.
- manual_outcomes.py --transport-reviewed preparedSOURCEONLY:51additionalnonDNS interruptedmemberjobs identified, no actualnewreplacementscommittedyet. Runonlyaftercurrentqueueidle; originalcharges retained. Separate11olderunknownreplacement decisions alreadycommittedandcompiled.
- Currentnewarcher selection stillWhisperuncertain; profiles_impl diagnosing5othercontexts, thenrootScribeprobe whenbudgetidle. Do notclaimpronunciationapproved. Mayneedcharacterreplacement onlyifstrongerpilotfails.
- 40oldergoodperformance candidates previewed (20differentseed) in older-performance-preview.json; no promotion/sourcechanges. Rerunfreshafterqueue ifneeded.
- Final_audio.py/delivery.py now requirecurrent normalizedsource/provenance+independentlydecodedallWEMproof. encoding.compare samplesonlycurrent normalizedaccepted5representativefamilies; runcomparison AFTERnormalize, thenfinal_audio build (codehashcurrency).
- cleanup.py plus cleanup_author.py prepared, NOTEXECUTED. AuthorhelperonlyownedWwise.cache/validationcache/Pythonbytecode withrebuildproof; requiredsourcesprojectOriginals/ConversionSettings/SoundBanksprotected.
- Coverage correction SOURCEONLY pendingnextcompile: commonstop/hold/charge/aim/fireorders now target3takes (cappednative slots); previousheuristiconlyselect/move/attack/etc gave these2.3requirementtests pass. Nextjobcompilewillincreaseplannedrecordingcount; recomposeSCARexpectationmetadata/candidatebeforefinalZIP (audioonly+metadataslicepreserved).

## Current production checkpoint (UTC11:30 onward)
- Current plan5685jobs/20939nativealiases,101941characters; conservative baseline plus20% retry USD36.6988, unchanged hardceiling100. Other25actors frozen by casting-lock; only Archer recast to independently piloted MSA adult actor after weak original pronunciation. Five acoustic/ASR pilots passed; native pronunciation/listening pending.
- Session57010 stopped correctly on transport ambiguity:4676accepted,42review,43rejected,922unattempted,2failed. Offline partial recovery added33accepted, budget unchanged:4709accepted. Bounded quality preparation queued14retakes; two uncertain singles explicitly received separate seeded-performance decisions, with original reservations retained.
- Current paid coordinator execsession34875, fouractor workers. No other API/Budget writer. No final normalization/encoding/ZIP/cleanup performed yet.
- Reporting separates requestrecords from byteunique sources/native audio, and fallbackreuse never counts as new. Repair validates exactidentity+sourcehash and preserves seed/provenance history. Spend reports distinguish conservative reservations, known provider credit evidence and unknown outcome charges.
- Next: complete unattempted jobs, offline recovery/bounded quality repairs and documented exactcontext fallback gaps, normalize stockloudness, compare currentnormalized Wwise qualities, encode+independentlydecode allMedium, recompose exact051 metadata, package bothZIPs, verify and cleanup.

## Memory/key recovery checkpoint (UTC12:20 onward)
- Session34875 hit hostMemoryError; user saved/closed EssenceEditor (~15GBprivate). Only our verified blocked helper processes were stopped. HostWMI then hung SciPy platform imports; run_local.py supplies process-local CPython WMI fallback and BLAS/OMPthreads1. Use this wrapper for ALL Pythonhelpers on this host, including tests.
- Offline recovery added24clips; qualityhelper prepared63retakes. One hash-proved Archer PCM survivedMemoryError and was revalidated/accepted with originalreceiptbackup under memory-recovery. Eighteen interruptedjobs (4originalattemptreservations) explicitly receive separate seededperformances; originaluncertainreservations retained. Independent review verified allidentities and unchanged25otheractors.
- Newrun_queue.py dispatches only absentCURRENTreceiptkeys; cachedaccepted/failed/unknown untouched. Session87281 had483pending, but stopped after2explicit401refusals:5158accepted,44review,2failed,481unattempted. Oldkeyexpired; human suppliedreplacement in chat. Never echo/store credentials. Credentialloader reads latesthuman key from exactrootchat in memory.
- Current offline normalization execsession53691 on5158accepted (others skipped), stockgainonly, mastersuntouched. Do NOTstartgeneration untilnormalizationends. Current resume_credentials execsession19617 verifiesreplacementauth/read-only thenrequeues2explicit401+releasesonlyknownrefusalestimates; no paidcalls. Waitcompletion before anyotherBudgetwriter/plancompile.
- Controlleddelivery preview found41hash-provedclippedHIGHspoken jobs, estimate0.216USD and conservative totalincludingfullfuturebaseline93.3402USD<100. Excludes2normalVillagerlines+1nonverbaleffort. controlled_delivery.py/jobs.py optional performance-overrides stage source/tests ready, NOTAPPLIED. After normalizer+authhelperfinish: applycontrolledonce, compile, then run_queue.py workers2 or4; no genericupstreamepochchanges for alreadycontrolledjobs.
- Newunexpected actor exceptions abortglobaldispatch before rethrow;38focusedtests pass. Fullfinalsourcesuite207tests:205pass,2privilege skips,0failures. Deliverycounts distinguish acceptedrequests/byteunique sources/native/WEMpayloads, creditreservationvsinvoice, chronology/fallback/variation gaps. REBUILD includes run_local hostworkaround.
- Still NO finalWwiseallencode, ZIPs, realgameinstallation, audiblegameplay orcleanup. Normalization/currentrecordings reusable because futurequeue neverrestorescachedbatches. All finalhash/coverage/normalized/currentplan proofs stillrequired.

## Active final generation checkpoint (UTC12:45 onward)
- Replacement key read-onlyauthentication passed;2explicit401jobs requeued, only0.0117USDknownrefusalestimates released. Conservative reservations56.4137USD beforenewcalls. Human reports previous task usedonly4.60USD; this is humaninvoicecontext, not a reason to erase uncertain requestreservations or increase100USDcap.
- Firstnormalizationpass53691 completedon5158accepted/current5685jobs; losslessmasters unchanged, proofs/retainedpre-normalization inputs preserved. Futurepass now skips identicalreceiptwrites afterfullverification (11focusedtests pass).
- Controlledhelper77147 committed41clippedHIGHspoken replacements ([shouting]→[angry]); noeffort/normal/unknown substitution. Currentplan recompiled5685jobs101818chars estimatewith20%retry36.6545USD. Paidrun_queue39304active4actors withreplacementkey; ONLY coordinator maywriteBudget/API. Pending~524 currentjobrequests (inclcontrols/retakes/unattempted); stable cachednormalizedaccepted neverrestored.
- Credential/shutdownunknowns preserveoriginalreservations. All18memorydecisions and recoveredArcher independentlyverified. Sourcequality stillrejectsclipping; somereusedtakefallbacks mayremainnecessary and mustnotcount asnewrecordings.
- CSVcurrency improvement sourcework underway: deliverymust regenerate actor/prompt/currentplan-bounddialogueregister beforeZIP, includingcontrolledpromptchanges. Finalregister maynotbe stalefromoriginal5339jobroster.
