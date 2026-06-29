
Uniform Appraisal Dataset (UAD) 3.6 Job Aid 
Guidance for Appraisers through Lessons Learned 
Issued by Fannie Mae and Freddie Mac 
Document Version 1.0 
June 23, 2026
This document relates to the Uniform Mortgage Data Program®, an effort undertaken jointly by Freddie Mac and Fannie Mae at the direction of U.S. Federal  Housing (FHFA). 
© 2026 Fannie Mae and Freddie Mac. Trademarks of the respective owners. 
Contents 
Revision History ............................................................................................................................................3 Introduction ..................................................................................................................................................3 Lessons Learned Examples............................................................................................................................4 
1. Utilizing the Correct Rows on the Sales Comparison Grid...............................................................4 a. Subject Property has an Inground Pool.......................................................................................4 b. Property Amenities......................................................................................................................5 c. Transfer Terms and Financing Type.............................................................................................7 d. Site Influence...............................................................................................................................8 
2. Completing the Area Breakdown within the Unit Interior Section .................................................9 3. Completing the Level and Room Detail within the Unit Interior Section ......................................10 4. Uploading Legible Exhibits.............................................................................................................11 5. Ensuring Accuracy in Exhibit Captions...........................................................................................12 6. Uploading Exhibits to the Applicable Sections of the Appraisal Report........................................13 7. Comparable Weight.......................................................................................................................14 8. New 3.6 Terminology for Area.......................................................................................................15 9. Significant Real Property Appraisal Assistance..............................................................................16 10. Inconsistencies in reporting Condition ..........................................................................................17 11. New Construction Update Status ..................................................................................................18
2 
Revision History 
Date 
Version # 
Description
June 23, 2026 
1.0 
Initial publication


Introduction 
This document supports appraisers by summarizing key observations from initial UAD 3.6 appraisal  reports. This document also helps lenders as they review the new Uniform Residential Appraisal Report (URAR). While adopting UAD 3.6 may present a learning curve, exploring practical examples such as how  certain data elements should be reported – will enhance clarity and understanding of the redesign.  Understanding the changes associated with UAD 3.6 will promote consistency and accuracy across all  appraisal submissions.
3 
Lessons Learned Examples 
1. Utilizing the Correct Rows on the Sales Comparison Grid 
In several sections of the new Sales Comparison Approach grid (“sales grid”), an additional row, referred  to as the "blank" row, is available for cases where a specific characteristic requiring an adjustment does  not have a predefined row.  
• This blank row should only be used after thoroughly reviewing all available rows, as some may  not be immediately visible in your software without locating the mechanism to display all  available predefined rows.  
• It is crucial to use the predefined row whenever possible because it ensures the correct data is  generated in the XML and provides the correct list of valid values.  
• Familiarize yourself with your software's functionality for selecting from the predefined list and  verify that the feature you wish to add is not already available before opting to use an additional  blank row. 
Due to the expandable nature of the sales grid: 
• Do not report the same information more than once in the sales grid. 
• Do not duplicate line items and/or their adjustments. 
Below are examples of an incorrect way and the correct way to incorporate different rows into the grid. a. Subject Property has an Inground Pool 
Below is an example of an Inground Pool being included within the grid in the incorrect/unrelated  subsection (i.e., Unit(s) subsection): 
Non-Compliant
The Inground Pool should be added as a line item within the Property Amenities subsection of the sales grid as a Water Feature (this is where the adjustment should be made): 
Compliant 
4 
b. Property Amenities 
Within the General Information section of the sales grid, the appraiser added two new lines:  • Porch/Patio/Deck 
• Other (In this example, the appraiser used this line to capture the Inground Pool for Comparable  #3) 
Non-Compliant
Porches, patios, and decks along with inground pools should be captured in the Property Amenities section of the SCA grid. Porches, patios, and decks are Outdoor Living features while inground pools are  Water Features. 
5 
Below is an example from Single-Family Scenario 1 on how to properly include Outdoor Living and  Water Features within the Property Amenities section of the SCA grid. If there is a covered or screened patio or porch, you should utilize the available enumerations and then use the commentary to provide  the additional detailed characteristics about the amenity.  
Compliant 
In the example below, the appraiser chose to include both the Outdoor Living and Whole Home line  items within the Property Amenities section of the SCA grid but did not include any of the information  for the subject or comparables.  
Non-Compliant
When features such as Property Amenities are not applicable to the subject or comparables, the  appraiser should not include them on the SCA grid. 
6 
c. Transfer Terms and Financing Type 
In the example below, the appraiser indicated that the Financing Type for all three Comparables was  Arm’s Length Conventional. Because this is not an allowable enumeration, the appraiser selected the  Other (Describe) option and manually typed it in. 
In this scenario, Typically Motivated should be selected in the Transfer Terms row, as it is defined as arm’s length. These are separate line items that should not be conflated with one another.  
Non-Compliant 
In this case, the appraiser should have simply used the allowable enumeration of Conventional for the  Financing Type line item.  
Compliant
7 
d. Site Influence 
The example below depicts the Site Influence subsection as well as the SCA grid. Instead of choosing  one of the allowable enumerations, the appraiser selected Other and manually typed in their own  description which resulted in non-compliant entries both the subject and all comparables: 
Non-Compliant 
Appendix F-1: URAR Reference Guide includes detailed lists of enumerations and their definitions for  data fields found throughout the appraisal report. In this case, the appraiser should have selected  the Residential enumeration which appears to align with what they manually entered: 
Compliant
8 
2. Completing the Area Breakdown within the Unit Interior Section 
When completing the Area Breakdown subsection, ensure that the standard and nonstandard areas (if  exists) are reported correctly/not duplicated. Below depicts an example where the finished area was  mistakenly duplicated as both standard AND nonstandard: 
Non-Compliant
Standard and Nonstandard finished areas are reported separately in the Area Breakdown subsection.  Compliant 
When reporting the Area Breakdown totals within the Unit Interior section of the appraisal report, the  appraiser is required to include each of the area types that apply for the subject. When it is reported  that the subject has unfinished and/or nonstandard area(s), this should also be included within the sales  comparison grid.  
9 
3. Completing the Level and Room Detail within the Unit Interior Section 
Within the Unit Interior section, the Levels in Unit and the Level and Room Detail are required to  match. Below is an example of there being a discrepancy between these two fields. Please note that the  below grade area is considered a level: 
Non-Compliant 
Always confirm that the Levels in Unit reflects the number of rows in the Level and Room Detail table.  The levels should be listed in order from lowest to highest level. Below is a screenshot from the URAR  Reference Guide: 
Compliant
10 
4. Uploading Legible Exhibits 
When including exhibits within the appraisal report, ensure that the images are legible. Below is an  example of an unclear/obscure Market Exhibits being included in an appraisal report: 
Non-Compliant
If images upload as unclear/obscure in the appraisal report, the appraiser should contact the appraisal  software provider’s technical support in effort to remediate the issue. 
11 
5. Ensuring Accuracy in Exhibit Captions 

When including exhibits within the appraisal report, captions should be concise, relevant, and clearly  describe what is shown in the image. Above is an example of Unit Interior exhibits that were correctly  given enumerated captions; however, additional free‑form commentary was added resulting in  unnecessary duplicate/conflicting labels which may cause confusion for reviewers: 
Please refer to the URAR Reference Guide: 
• “Photos or images relevant to the (Applicable) section may be provided, which display in  (Applicable) Exhibits subsection. If the photo or image is not specifically indicated above,  provide a caption to identify each photo or image.”
12 
6. Uploading Exhibits to the Applicable Sections of the Appraisal Report 
When including exhibits within the appraisal report, refrain from uploading images to non-applicable  sections. Below is an example of Unit Interior Exhibits being uploaded to the Subject Property section  of the report: 

Ensure that the exhibits included are relevant to the section they are being uploaded to (i.e., Unit  Interior Exhibits being uploaded to the Unit Interior section of the report): 
For more information, refer to the UAD Job Aid: Photo and Image Requirements.
13 
7. Comparable Weight  
UAD 3.6 now captures the Comparable Weight data field in the Sales Comparison Approach section. 
Given that this now populates on the sales grid, it is essential for any commentary included within the  Reconciliation of Sales Comparison Approach subsection to align with the Comparable Weight that was  reported. Below is an example of familiar UAD 2.6 “canned commentary” that does not align with what  was reported on the sales grid:

14 
8. New 3.6 Terminology for Area  
UAD 3.6 has introduced new terminology when describing the area of a property – see below for the  Area Breakdown from Appendix F-1: URAR Reference Guide: 

Some of the familiar terms from UAD 2.6 are no longer represented in UAD 3.6. One of the more  significant examples of this is Gross Living Area (GLA). Below is an example of familiar UAD 2.6 “canned  commentary” that does not align with the new UAD 3.6 terminology:
15 
9. Significant Real Property Appraisal Assistance 
The Significant Real Property Appraisal Assistance subsection of the Assignment Information section  provides details about people who provided significant real property appraisal assistance to the  appraiser. Below is an example of this subsection being filled out incorrectly with guidance provided on  the noted issues: 
Non-Compliant

In order to better understand how to complete Significant Real Property Appraisal Assistance subsection (when applicable), please refer to the Assignment Information section of Appendix F-1:  URAR Reference Guide. In addition to this, Appendix D-1: URAR Sample Scenarios and XML Files include Single Family Scenario 1 which includes an example of how to complete correctly. 
16 
10. Inconsistencies in reporting Condition 
Appraiser noted that there are missing floor coverings in multiple rooms of the subject. They included  these in the Defects, Damages, and Deficiencies (Unit Interior) table, but indicated that the  recommended actions were None. By definition as seen in Appendix F-1: URAR Reference Guide,  missing floor coverings should result in a C5 rating: 

• If this is intended to be an as-is appraisal due to the missing floor coverings, by definition this  would be a C5. 
• If the appraisal was intended to be made subject to the installation of the floor coverings, then it  could be made a C4.
17 
11. New Construction Update Status 
When a home is a New Construction, the Update Status for Kitchens and Baths, Overall Update Status  for Bathrooms and the Overall Update Status for Flooring should reflect Fully Updated. This is a  departure from UAD 2.6 which guides the appraiser to select Not Updated.  
Non-CompliantNote: Ensure that if it is New Construction, it meets the definition of New Construction and Fully  
Updated is selected in order to represent the property as C1. This is a change from how this was  reported using UAD 2.6. 
18 