' test eurlex fetching and parsing code '
import os
import wetsuite.datacollect.eurlex
import wetsuite.helpers.net


def test_extract_html():
    ''' test whether parsing basically works. 
        TODO: more cases that deal with absence of parts, and more coverage of details.
    '''
    #htmlbytes = wetsuite.helpers.net.download('https://eur-lex.europa.eu/eli/reg/2016/679/oj')
    import test_eurlex   #import for self-reference is intentional, pylint: disable=W0406
    with open( os.path.join( os.path.dirname( test_eurlex.__file__ ),'eurlex.html' ), 'rb') as f:
        htmlbytes = f.read()
    d = wetsuite.datacollect.eurlex.extract_html( htmlbytes )
    assert d['celex'] == '32016R0679'


def test_fetch_by_resource_type():
    ' test that fetching from the sparql API does not return an error (does not do anything with the data) '
    wetsuite.datacollect.eurlex.fetch_by_resource_type('LET') # choosing something with very little output
    # bindings = ret.get('results').get('bindings')
    #
    # for item_dict in bindings:
    #     url = item_dict.get('work').get('value')


### for reference, as of somewhere late 2023:
#
#      0   ABSTRACT_JUR                     Abstract
#      2   ACKNOWLEDGE_RECP                 Acknowledgement receipt
#      8   ACT                              Act
#      0   ACT_ADOPT_INTERNATION            Acts adopted by bodies created by international agreements
#     43   ACT_DRAFT                        Draft act
#   3.5K   ACT_LEGIS                        Legislative acts
#      0   ACT_LEGIS_NO                     Non-legislative acts
#    364   ACT_OTHER                        Other acts
#     2K   ACT_PREP                         Preparatory act - (pl. Preparatory acts)
#     21   ADD                              Addendum - (pl. Addenda)
#   1.7K   ADOPT_TEXT                       Texts adopted
#     17   AGREE                            Agreement
#      0   AGREE_ADDIT                      Additional agreement
#     62   AGREE_AMEND                      Amendment to an agreement
#      5   AGREE_EUMS                       Agreement between Member States - (pl. Agreements between Member States)
#      0   AGREE_EUMS_DRAFT                 Draft agreement between Member States
#     54   AGREE_INTERINSTIT                Interinstitutional agreement - (pl. Interinstitutional agreements)
#      0   AGREE_INTERINSTIT_DRAFT          Draft interinstitutional agreement
#     47   AGREE_INTERNAL                   Internal agreement
#   2.9K   AGREE_INTERNATION                International agreement - (pl. International agreements)
#      0   AGREE_INTERNATION_DRAFT          Draft international agreement
#    401   AGREE_PROT                       Protocol to the agreement
#      0   AGREE_UBEREINKOM                 Agreement between Member States - (pl. Agreements between Member States)
#      0   AGREE_UBEREINKOM_DRAFT           Draft agreement
#      0   AGREE_VEREINB                    Agreement
#     16   AID_STATE                        State aid
#      7   AMEND_PROP                       Amended proposal
#    441   AMEND_PROP_DEC                   Amended proposal for a decision
#     1K   AMEND_PROP_DIR                   Amended proposal for a directive
#   0.9K   AMEND_PROP_REG                   Amended proposal for a regulation
#      8   ANNEX                            Annex - (pl. Annexes)
#      0   ANNEX_SUM                        Annex summary
#  13.4K   ANNOUNC                          Announcements
#      0   ARCHIVE_FILE                     Archive file
#     51   ARRANG                           Arrangement
#     1K   ASSENT                           Assent
#      5   ASSENT_REQ                       Request for assent
#     73   BALANCE                          Balance
#   2.3K   BUDGET                           Budget - (pl. Budgets)
#    210   BUDGET_DRAFT                     Draft budget
#      9   BUDGET_DRAFT_PRELIM              Preliminary draft budget
#      5   BUDGET_DRAFT_PRELIM_SUPPL        Preliminary draft supplementary budget
#    120   BUDGET_DRAFT_SUPPL_AMEND         Draft supplementary and amending budget
#    556   BUDGET_SUPPL_AMEND               Supplementary and amending budget
#      8   CALL_EXPR_INTEREST               Call for expression of interest
#   1.6K   CALL_PROP                        Call for proposals
#      0   CASE                             Case
#  12.1K   CASE_LAW                         Reports of cases
#      0   CENSURE                          Censure
#      2   CENSURE_RJ                       Rejected motion of censure
#      2   CENSURE_WDW                      Withdrawn motion of censure
#      0   CITIZ_SUM                        Citizens’ summary
#    19K   COMMUNIC                         Communication
#      3   COMMUNIC_DRAFT                   Draft communication
#    512   COMMUNIC_POSIT                   Communication concerning the position of the Council
#   1.3K   COMPOS                           Common position
#    391   COMPOS_ACCEPT                    Acceptance of common position
#    521   COMPOS_AMEND                     Amendment to common position
#      0   COMPOS_DRAFT                     Draft common position
#      9   COMPOS_RJ                        Rejection of the common position
#      0   COMPOS_RJ_CONFIRM                Confirmation of the rejection of the common position
#    358   CONCL                            Conclusions
#    30K   CONS_TEXT                        Consolidated text
#    143   CONVENTION                       Convention
#      0   CORRIGENDUM                      Corrigendum - (pl. Corrigenda)
#    69K   DATPRO                           Provisional data
#    20K   DEC                              Decision - (pl. Decisions)
#    637   DECLAR                           Declaration
#      0   DECLAR_DRAFT                     Draft declaration
#     64   DEC_DEL                          Delegated decision
#     11   DEC_DEL_DRAFT                    Draft delegated decision
#    529   DEC_DRAFT                        Draft decision
#    33K   DEC_ENTSCHEID                    Decision
#     34   DEC_FRAMW                        Framework decision
#      0   DEC_FRAMW_DRAFT                  Draft framework decision
#   3.9K   DEC_IMPL                         Implementing decision
#     97   DEC_IMPL_DRAFT                   Draft implementing decision
#    35K   DEC_NC                           Decision by national courts in the field of European Union law
#      7   DEC_REVIEW                       Decision to review
#   4.2K   DIR                              Directive - (pl. Directives)
#    169   DIR_DEL                          Delegated directive
#     66   DIR_DEL_DRAFT                    Draft delegated directive
#     97   DIR_DRAFT                        Draft directive
#     88   DIR_IMPL                         Implementing directive
#     12   DIR_IMPL_DRAFT                   Draft implementing directive
#    136   EXCH_LET                         Exchange of letters
#   5.5K   EXCH_RATE                        Exchange rate
#    106   EXCH_RATE_MRO                    Interest rate — euro exchange rates
#      0   FORM_OJ_TOC                      Request form for the table of contents of the Official Journal
#      0   FORM_PPF                         Form for print production file
#      0   FORM_REQ_PRE_PRESS               Request form for pre-press of publication
#      0   FORM_REQ_PUB                     Request form for publication
#      0   FORM_REQ_PUB_ACCEPT              Request form for the acceptance of publication
#      0   FORM_REQ_PUB_REFUS               Request form for the refusal of publication
#      0   FORM_REQ_READY_PRESS             Request form for the ready-for-press of publication
#     31   GARNISHEE_ORDER                  Attachment order
#    345   GLOS_TERM                        Glossary term
#    241   GUIDELINE                        Guideline - (pl. Guidelines)
#     43   GUIDELINE_GEN                    General guidelines
#      4   GUIDELINE_LIGNES                 Guideline
#   1.1K   IMPACT_ASSESS                    Impact assessment
#    312   IMPACT_ASSESS_INCEP              Inception impact assessment
#     1K   IMPACT_ASSESS_SUM                Summary of impact assessment
#   2.1K   INFO                             Information
#   5.2K   INFO_COMMUNIC                    Information
#      0   INFO_GEN                         General information - (pl. General informations)
#    63K   INFO_JUDICIAL                    Judicial information
#   9.5K   INFO_JUR                         Information
#      0   INFO_SPECIAL                     Special information
#      0   INFO_SUPPL                       Supplementary information
#    122   INI                              Initiative
#      0   INTRO_TEXT                       Introductory text
#      0   ITEM_A_LIST                      List of ‘A’ items
#      0   ITEM_A_LIST_ADP                  List of adopted ‘A’ items
#      0   ITEM_A_LIST_PROVIS               Provisional list of ‘A’ items
#    152   ITEM_A_NOTE                      ‘A’ item note
#   2.2K   ITEM_IA_NOTE                     ‘I/A’ item note
#    615   ITEM_I_NOTE                      ‘I’ item note
#    340   JOINT_ACTION                     Joint action
#      0   JOINT_ACTION_DRAFT               Draft joint action
#     92   JOINT_COMMUNIC                   Joint communication
#      2   JOINT_DEC                        Joint decision
#      2   JOINT_IMPACT_ASSESS              Joint impact assessment
#      2   JOINT_IMPACT_ASSESS_SUM          Joint impact assessment summary
#      0   JOINT_PAPER_GREEN                Joint Green Paper
#      0   JOINT_PAPER_WHITE                Joint White Paper
#     53   JOINT_PROP_DEC                   Joint proposal for a decision
#      0   JOINT_PROP_DIR                   Joint proposal for a directive
#    127   JOINT_PROP_REG                   Joint proposal for a regulation
#     54   JOINT_REPORT                     Joint report
#    109   JOINT_SWD                        Joint staff working document
#      3   JOINT_TEXT                       Joint text
#    150   JOINT_TEXT_APR                   Approved joint text
#      3   JOINT_TEXT_RJ                    Rejected joint text
#    23K   JUDG                             Judgment
#     16   JUDG_EXTRACT                     Judgment (extracts)
#   5.1K   LEGIS_SUM                        Summaries of EU legislation
#     13   LET                              Letter
#     22   LET_AMEND                        Letter of amendment
#    301   LIST                             List
#   276K   MEAS_NATION_IMPL                 National implementing measures
#      0                                    National transposition measures
#     51   MEMORANDUM                       Memorandum
#    124   MEMORANDUM_UNDERST               Memorandum of understanding
#   1.2K   MINUTES                          Minutes
#     20   MINUTES_DRAFT                    Draft minutes
#   4.4K   NOTE                             Note
#   4.4K   NOTE_COVER                       Cover note
#   1.2K   NOTE_INFO                        Information note
#    16K   NOTICE                           Notice
#     44   NOTICE_AWARD                     Award notice
#   1.8K   NOTICE_CONTRACT                  Contract notice
#      2   NOTICE_INFO                      Notice - (pl. Notices)
#     34   NOTICE_MODEL_PP                  Model notice for public procurement
#    864   NOTICE_READER                    Notice to readers
#    551   NOTIF                            Notification
#    45K   OJ                               Official Journal
#   4.2K   OJ_SPECIAL                       Special edition of the Official Journal
#  11.4K   OPIN                             Opinion - (pl. Opinions)
#     49   OPIN_ADDIT                       Additional opinion
#  10.8K   OPIN_AG                          Opinion of the Advocate General
#    424   OPIN_AMEND_EP                    Opinion on the European Parliament’s amendments
#      0   OPIN_CASE                        Advocate general’s opinion
#     31   OPIN_DISPUT_LB                   Opinion disputing a legal base
#    242   OPIN_EXPLOR                      Exploratory opinion
#    310   OPIN_IMPACT_ASSESS               Opinion on impact assessment
#     12   OPIN_JUR                         Opinion of the Court
#     3K   OPIN_NO_PROP_AMEND               Opinion not proposing amendment
#    677   OPIN_NO_REPORT                   Opinion without report
#   3.5K   OPIN_PROP_AMEND                  Opinion proposing amendment
#    100   OPIN_PROP_RJ                     Opinion proposing rejection
#    266   OPIN_QUAL_APR                    Opinion with qualified approval
#   6.4K   ORDER                            Order
#      0   ORDER_EXTRACT                    Order (extracts)
#     2K   OWNINI_OPIN                      Own-initiative opinion
#     29   OWNINI_OPIN_ADDIT                Additional own-initiative opinion
#   3.5K   OWNINI_REPORT                    Own-initiative report
#   6.9K   OWNINI_RES                       Own-initiative resolution
#    155   PAPER_GREEN                      Green Paper
#      6   PAPER_REFLEC                     Reflection paper
#     40   PAPER_WHITE                      White Paper
#      0   PETITION                         Petition
#      0   PLANNING_DOC                     Planning document
#    196   POSIT                            Position
#      0   POSIT_ACCEPT                     Acceptance of position
#      0   POSIT_AMEND                      Amendment to position
#      0   POSIT_RJ                         Rejection of position
#      0   POSIT_RJ_CONF                    Confirmation of the rejection of the position
#      0   PRESS_REL                        Press release
#     66   PROCEED_MINUTES                  Minutes of proceeding
#     23   PROC_ADMIN                       Administrative procedures
#    237   PROC_INTERNAL                    Rules of procedure
#      0   PROC_JURIS                       Jurisdictional procedure - (pl. Jurisdictional procedures)
#     93   PROC_RULES                       Rules of procedure
#     59   PROGRAM                          Programme
#   3.7K   PROP_ACT                         Proposal for an act
#      1   PROP_AMEND                       Amendments to the proposal
#      0   PROP_COMPOS                      Proposal for a common position
#   3.7K   PROP_DEC                         Proposal for a decision
#      0   PROP_DECLAR                      Proposal for a declaration
#      0   PROP_DEC_FRAMW                   Proposal for a framework decision
#    317   PROP_DEC_IMPL                    Proposal for an implementing decision
#     4K   PROP_DEC_NO_ADDRESSEE            Proposal for a decision without addressee
#   2.9K   PROP_DIR                         Proposal for a directive
#      0   PROP_DIR_IMPL                    Proposal for an implementing directive
#     14   PROP_DRAFT                       Draft proposal
#      7   PROP_JOINT_ACTION                Proposal for a joint action
#      7   PROP_OPIN                        Proposal for an opinion
#    157   PROP_RECO                        Proposal for a recommendation
#  12.7K   PROP_REG                         Proposal for a regulation
#     52   PROP_REG_IMPL                    Proposal for an implementing regulation
#      5   PROP_RES                         Proposal for a resolution
#   1.2K   PROT                             Protocol
#      0   PROT_DRAFT                       Draft protocol
#   126K   PUB_GEN                          General publications
#   2.5K   QUEST_ORAL                       Oral question - (pl. Oral questions)
#    21K   QUEST_TIME                       Question at question time - (pl. Questions at question time)
#   174K   QUEST_WRITTEN                    Written question - (pl. Written questions)
#   2.3K   RECO                             Recommendation - (pl. Recommendations)
#    797   RECO_DEC                         Recommendation for a decision
#      0   RECO_DIR                         Recommendation for a directive
#     24   RECO_DRAFT                       Draft recommendation
#      0   RECO_OPIN                        Recommendation for an opinion
#    271   RECO_RECO                        Recommendation for a recommendation
#    156   RECO_REG                         Recommendation for a regulation
#      0   RECO_RES                         Recommendation for a resolution
#    805   RECRUIT                          Recruitment
#      0   REFERRAL_LET                     Referral letter
#   131K   REG                              Regulation - (pl. Regulations)
#   1.9K   REG_DEL                          Delegated regulation
#    438   REG_DEL_DRAFT                    Draft delegated regulation
#    533   REG_DRAFT                        Draft regulation
#     73   REG_FINANC                       Financial regulation
#  10.3K   REG_IMPL                         Implementing regulation
#    469   REG_IMPL_DRAFT                   Draft implementing regulation
#      0   REPLY_OPIN_NP                    Reply to national Parliaments’ opinion
#   8.7K   REPORT                           Report
#      0   REPORT_AAR                       Annual activity report
#     51   REPORT_ANNUAL                    Annual report
#      3   REPORT_ANNUAL_BUDGET             Annual report on the EU general budget
#     16   REPORT_ANNUAL_DAS                Annual report with the statement of assurance
#      3   REPORT_ANNUAL_EDF                Annual report on the activities funded by the European Development Fund
#    129   REPORT_ANNUAL_SPECIF             Specific annual report
#      0   REPORT_PERIOD                    Periodic report
#      0   REPORT_SEMEST                    Six-monthly report
#    467   REPORT_SPECIAL                   Special report
#      0   REPORT_SPECIF                    Specific report
#      0   REPORT_VALID                     Validation report
#   4.6K   RES                              Resolution - (pl. Resolutions)
#     47   RES_DRAFT                        Draft resolution
#   1.9K   RES_LEGIS                        Legislative resolution
#    296   ROADMAP                          Roadmap
#    195   ROADMAP_EFC                      Evaluation and Fitness Check Roadmap
#      1   RULING                           Ruling
#  11.8K   SIGN_OJ_ATC                      Signature file for the authentic Official Journal
#     60   STAT                             Statement
#     28   STATUTE                          Statute
#    199   STAT_REASON                      Statement of reasons
#    114   STAT_REASON_DRAFT                Draft statement of reasons
#      5   STRATEGY_COMMON                  Common strategy
#    16K   STU                              Study
#   1.2K   STU_ANNEX                        Annex to a study
#    565   STU_EVL                          Evaluation study
#     82   STU_EVL_ANNEX                    Annex to an evaluation study
#    117   STU_EVL_SUM_EXE                  Executive summary of an evaluation study
#   1.6K   STU_SUM_EXE                      Executive summary of a study
#    658   SUM                              Summary
#    22K   SUM_JUR                          Summary
#   3.5K   SWD                              Staff working document
#     12   THIRDPARTY_PROCEED               Third-party proceedings
#    45K   TOC_OJ                           Contents
#   4.2K   TOC_OJ_SPECIAL                   Contents of the Special edition of the Official Journal
#     90   TRANSFER_APPROPR                 Transfer of appropriations
#   8.3K   TREATY                           Treaty - (pl. Treaties)
#      0   TREATY_DRAFT                     Draft treaty
#      0   VIEW                             View
#      0   VIEWPOINT                        Viewpoint
#     27   VIEW_AG                          View of the Advocate General
#     19   WARN                             Warning - (pl. Warnings)
#      0   WEBPAGE                          Webpage
#      0   WEBSITE                          Website
#      0   WORK_BUNDLE                      Work bundle
#    134   WORK_DOC                         Working document
