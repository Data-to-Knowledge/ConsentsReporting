USE ConsentsReporting;


/************ Update: Schemas ***************/

/* Add Schema: dbo */
CREATE SCHEMA dbo;



/************ Update: Tables ***************/

/******************** Add Table: dbo.Activity ************************/

/* Build Table Structure */
CREATE TABLE dbo.Activity
(
	ActivityID INTEGER IDENTITY (1, 1) NOT NULL,
	ActivityType VARCHAR(19) NOT NULL,
	HydroFeatureID INTEGER NOT NULL,
	Description VARCHAR(299) NULL,
	ModifiedDate DATETIME DEFAULT getdate() NOT NULL
);

/* Add Primary Key */
ALTER TABLE dbo.Activity ADD CONSTRAINT pkActivity
	PRIMARY KEY (ActivityID);


/******************** Add Table: dbo.AlloBlock ************************/

/* Build Table Structure */
CREATE TABLE dbo.AlloBlock
(
	AlloBlockID INTEGER IDENTITY (1, 1) NOT NULL,
	AllocationBlock VARCHAR(19) NOT NULL,
	HydroFeatureID INTEGER NOT NULL,
	Description VARCHAR(299) NULL,
	ModifiedDate DATETIME DEFAULT getdate() NOT NULL
);

/* Add Primary Key */
ALTER TABLE dbo.AlloBlock ADD CONSTRAINT pkAlloBlock
	PRIMARY KEY (AlloBlockID);


/******************** Add Table: dbo.AllocationRate ************************/

/* Build Table Structure */
CREATE TABLE dbo.AllocationRate
(
	AlloVolID INTEGER NOT NULL,
	Month INTEGER NOT NULL,
	AllocatedRate FLOAT NOT NULL,
	ModifiedDate DATETIME DEFAULT getdate() NOT NULL
);

/* Add Primary Key */
ALTER TABLE dbo.AllocationRate ADD CONSTRAINT pkAllocationRate
	PRIMARY KEY (Month, AlloVolID);


/******************** Add Table: dbo.AllocationVolume ************************/

/* Build Table Structure */
CREATE TABLE dbo.AllocationVolume
(
	AlloVolID INTEGER IDENTITY (1, 1) NOT NULL,
	RecordNumber VARCHAR(19) NOT NULL,
	AlloBlockID INTEGER NOT NULL,
	SiteID INTEGER NOT NULL,
	AllocatedAnnualVolume INTEGER NOT NULL,
	FromMonth INTEGER NOT NULL,
	ToMonth INTEGER NOT NULL,
	ModifiedDate DATETIME DEFAULT getdate() NOT NULL
);

/* Add Primary Key */
ALTER TABLE dbo.AllocationVolume ADD CONSTRAINT pkAllocationVolume
	PRIMARY KEY (AlloVolID);


/******************** Add Table: dbo.Attributes ************************/

/* Build Table Structure */
CREATE TABLE dbo.Attributes
(
	AttributeID INTEGER IDENTITY (1, 1) NOT NULL,
	Attribute VARCHAR(50) NOT NULL,
	Description VARCHAR(299) NULL,
	ModifiedDate DATETIME DEFAULT getdate() NOT NULL
);

/* Add Primary Key */
ALTER TABLE dbo.Attributes ADD CONSTRAINT pkAttributes
	PRIMARY KEY (AttributeID);


/******************** Add Table: dbo.ConsentedAttributes ************************/

/* Build Table Structure */
CREATE TABLE dbo.ConsentedAttributes
(
	ConsentVolID INTEGER NOT NULL,
	AttributeID INTEGER NOT NULL,
	Value VARCHAR(299) NOT NULL,
	ModifiedDate DATETIME DEFAULT getdate() NOT NULL
);

/* Add Primary Key */
ALTER TABLE dbo.ConsentedAttributes ADD CONSTRAINT pkConsentedAttributes
	PRIMARY KEY (AttributeID, ConsentVolID);


/******************** Add Table: dbo.ConsentedRatesVolumes ************************/

/* Build Table Structure */
CREATE TABLE dbo.ConsentedRatesVolumes
(
	ConsentVolID INTEGER IDENTITY (1, 1) NOT NULL,
	RecordNumber VARCHAR(19) NOT NULL,
	ActivityID INTEGER NOT NULL,
	SiteID INTEGER NOT NULL,
	Rate FLOAT NOT NULL,
	MultiDayVolume INTEGER NULL,
	MultiDayPeriod INTEGER NULL,
	AnnualVolume INTEGER NULL,
	FromMonth INTEGER NOT NULL,
	ToMonth INTEGER NOT NULL,
	ModifiedDate DATETIME DEFAULT getdate() NOT NULL
);

/* Add Primary Key */
ALTER TABLE dbo.ConsentedRatesVolumes ADD CONSTRAINT pkConsentedRatesVolumes
	PRIMARY KEY (ConsentVolID);


/******************** Add Table: dbo.ConsentsSites ************************/

/* Build Table Structure */
CREATE TABLE dbo.ConsentsSites
(
	SiteID INTEGER IDENTITY (1, 1) NOT NULL,
	ExtSiteID VARCHAR(19) NOT NULL,
	SiteType VARCHAR(19) NOT NULL,
	Geo IMAGE NULL,
	ModifiedDate DATETIME DEFAULT getdate() NOT NULL
);

/* Add Primary Key */
ALTER TABLE dbo.ConsentsSites ADD CONSTRAINT pkConsentsSites
	PRIMARY KEY (SiteID);


/******************** Add Table: dbo.HydroFeature ************************/

/* Build Table Structure */
CREATE TABLE dbo.HydroFeature
(
	HydroFeatureID INTEGER IDENTITY (1, 1) NOT NULL,
	HydroFeature VARCHAR(19) NOT NULL,
	ModifiedDate DATETIME DEFAULT getdate() NOT NULL
);

/* Add Primary Key */
ALTER TABLE dbo.HydroFeature ADD CONSTRAINT pkHydroFeature
	PRIMARY KEY (HydroFeatureID);


/******************** Add Table: dbo.LinkedPermits ************************/

/* Build Table Structure */
CREATE TABLE dbo.LinkedPermits
(
	RecordNumber VARCHAR(19) NOT NULL,
	OtherRecordNumber VARCHAR(19) NOT NULL,
	Relationship VARCHAR(29) NOT NULL,
	CombinedAnnualVolume INTEGER NOT NULL,
	Status VARCHAR(59) NULL,
	ModifiedDate DATETIME DEFAULT getdate() NOT NULL
);

/* Add Primary Key */
ALTER TABLE dbo.LinkedPermits ADD CONSTRAINT pkLinkedPermits
	PRIMARY KEY (RecordNumber, Relationship, OtherRecordNumber);


/******************** Add Table: dbo.MonitoringSites ************************/

/* Build Table Structure */
CREATE TABLE dbo.MonitoringSites
(
	RecordNumber VARCHAR(19) NOT NULL,
	SiteID INTEGER NOT NULL,
	SiteRestrictionType VARCHAR(99) NOT NULL,
	ModifiedDate DATETIME DEFAULT getdate() NOT NULL
);

/* Add Primary Key */
ALTER TABLE dbo.MonitoringSites ADD CONSTRAINT pkMonitoringSites
	PRIMARY KEY (RecordNumber, SiteID);


/******************** Add Table: dbo.ParentChild ************************/

/* Build Table Structure */
CREATE TABLE dbo.ParentChild
(
	ParentRecordNumber VARCHAR(19) NOT NULL,
	ChildRecordNumber VARCHAR(19) NOT NULL,
	ModifiedDate DATETIME DEFAULT getdate() NOT NULL
);

/* Add Primary Key */
ALTER TABLE dbo.ParentChild ADD CONSTRAINT pkParentChild
	PRIMARY KEY (ParentRecordNumber, ChildRecordNumber);


/******************** Add Table: dbo.Permit ************************/

/* Build Table Structure */
CREATE TABLE dbo.Permit
(
	RecordNumber VARCHAR(19) NOT NULL,
	ConsentStatus VARCHAR(29) NOT NULL,
	FromDate DATETIME NOT NULL,
	ToDate DATETIME NOT NULL,
	NZTMX INTEGER NOT NULL,
	NZTMY INTEGER NOT NULL,
	EcanID VARCHAR(9) NOT NULL,
	ModifiedDate DATETIME DEFAULT getdate() NOT NULL
);

/* Add Primary Key */
ALTER TABLE dbo.Permit ADD CONSTRAINT pkPermit
	PRIMARY KEY (RecordNumber);


/******************** Add Table: dbo.WAP ************************/

/* Build Table Structure */
CREATE TABLE dbo.WAP
(
	SiteID INTEGER NOT NULL,
	NZTMX INTEGER NOT NULL,
	NZTMY INTEGER NOT NULL,
	SD1_NZTMX INTEGER NULL,
	SD1_NZTMY INTEGER NULL,
	SD1_7day INTEGER NULL,
	SD1_30day INTEGER NULL,
	SD1_150day INTEGER NULL,
	SD2_NZTMX INTEGER NULL,
	SD2_NZTMY INTEGER NULL,
	SD2_7day INTEGER NULL,
	SD2_30day INTEGER NULL,
	SD2_150day INTEGER NULL,
	ModifiedDate DATETIME DEFAULT getdate() NOT NULL
);

/* Add Primary Key */
ALTER TABLE dbo.WAP ADD CONSTRAINT pkWAP
	PRIMARY KEY (SiteID);





/************ Add Foreign Keys ***************/

/* Add Foreign Key: fk_Activity_HydroFeature */
ALTER TABLE dbo.Activity ADD CONSTRAINT fk_Activity_HydroFeature
	FOREIGN KEY (HydroFeatureID) REFERENCES dbo.HydroFeature (HydroFeatureID)
	ON UPDATE NO ACTION ON DELETE NO ACTION;

/* Add Foreign Key: fk_AlloBlock_HydroFeature */
ALTER TABLE dbo.AlloBlock ADD CONSTRAINT fk_AlloBlock_HydroFeature
	FOREIGN KEY (HydroFeatureID) REFERENCES dbo.HydroFeature (HydroFeatureID)
	ON UPDATE NO ACTION ON DELETE NO ACTION;

/* Add Foreign Key: fk_AllocationRate_AllocationVolume */
ALTER TABLE dbo.AllocationRate ADD CONSTRAINT fk_AllocationRate_AllocationVolume
	FOREIGN KEY (AlloVolID) REFERENCES dbo.AllocationVolume (AlloVolID)
	ON UPDATE NO ACTION ON DELETE NO ACTION;

/* Add Foreign Key: fk_AllocationVolume_ConsentsSites */
ALTER TABLE dbo.AllocationVolume ADD CONSTRAINT fk_AllocationVolume_ConsentsSites
	FOREIGN KEY (SiteID) REFERENCES dbo.ConsentsSites (SiteID)
	ON UPDATE NO ACTION ON DELETE NO ACTION;

/* Add Foreign Key: fk_ConsentedAllocation_AlloBlock */
ALTER TABLE dbo.AllocationVolume ADD CONSTRAINT fk_ConsentedAllocation_AlloBlock
	FOREIGN KEY (AlloBlockID) REFERENCES dbo.AlloBlock (AlloBlockID)
	ON UPDATE NO ACTION ON DELETE NO ACTION;

/* Add Foreign Key: fk_ConsentedAllocation_Permit */
ALTER TABLE dbo.AllocationVolume ADD CONSTRAINT fk_ConsentedAllocation_Permit
	FOREIGN KEY (RecordNumber) REFERENCES dbo.Permit (RecordNumber)
	ON UPDATE NO ACTION ON DELETE NO ACTION;

/* Add Foreign Key: fk_ConsentedAttributes_Attributes */
ALTER TABLE dbo.ConsentedAttributes ADD CONSTRAINT fk_ConsentedAttributes_Attributes
	FOREIGN KEY (AttributeID) REFERENCES dbo.Attributes (AttributeID)
	ON UPDATE NO ACTION ON DELETE NO ACTION;

/* Add Foreign Key: fk_ConsentedAttributes_ConsentedRatesVolumes */
ALTER TABLE dbo.ConsentedAttributes ADD CONSTRAINT fk_ConsentedAttributes_ConsentedRatesVolumes
	FOREIGN KEY (ConsentVolID) REFERENCES dbo.ConsentedRatesVolumes (ConsentVolID)
	ON UPDATE NO ACTION ON DELETE NO ACTION;

/* Add Foreign Key: fk_ConsentedRatesVolumes_Activity */
ALTER TABLE dbo.ConsentedRatesVolumes ADD CONSTRAINT fk_ConsentedRatesVolumes_Activity
	FOREIGN KEY (ActivityID) REFERENCES dbo.Activity (ActivityID)
	ON UPDATE NO ACTION ON DELETE NO ACTION;

/* Add Foreign Key: fk_ConsentedRatesVolumes_ConsentsSites */
ALTER TABLE dbo.ConsentedRatesVolumes ADD CONSTRAINT fk_ConsentedRatesVolumes_ConsentsSites
	FOREIGN KEY (SiteID) REFERENCES dbo.ConsentsSites (SiteID)
	ON UPDATE NO ACTION ON DELETE NO ACTION;

/* Add Foreign Key: fk_ConsentedRatesVolumes_Permit */
ALTER TABLE dbo.ConsentedRatesVolumes ADD CONSTRAINT fk_ConsentedRatesVolumes_Permit
	FOREIGN KEY (RecordNumber) REFERENCES dbo.Permit (RecordNumber)
	ON UPDATE NO ACTION ON DELETE NO ACTION;

/* Add Foreign Key: fk_AssociatedPermits_Permit1 */
ALTER TABLE dbo.LinkedPermits ADD CONSTRAINT fk_AssociatedPermits_Permit1
	FOREIGN KEY (RecordNumber) REFERENCES dbo.Permit (RecordNumber)
	ON UPDATE NO ACTION ON DELETE NO ACTION;

/* Add Foreign Key: fk_AssociatedPermits_Permit2 */
ALTER TABLE dbo.LinkedPermits ADD CONSTRAINT fk_AssociatedPermits_Permit2
	FOREIGN KEY (OtherRecordNumber) REFERENCES dbo.Permit (RecordNumber)
	ON UPDATE NO ACTION ON DELETE NO ACTION;

/* Add Foreign Key: fk_MonitoringSites_ConsentsSites */
ALTER TABLE dbo.MonitoringSites ADD CONSTRAINT fk_MonitoringSites_ConsentsSites
	FOREIGN KEY (SiteID) REFERENCES dbo.ConsentsSites (SiteID)
	ON UPDATE NO ACTION ON DELETE NO ACTION;

/* Add Foreign Key: fk_MonitoringSites_Permit */
ALTER TABLE dbo.MonitoringSites ADD CONSTRAINT fk_MonitoringSites_Permit
	FOREIGN KEY (RecordNumber) REFERENCES dbo.Permit (RecordNumber)
	ON UPDATE NO ACTION ON DELETE NO ACTION;

/* Add Foreign Key: fk_ParentChild_Permit1 */
ALTER TABLE dbo.ParentChild ADD CONSTRAINT fk_ParentChild_Permit1
	FOREIGN KEY (ParentRecordNumber) REFERENCES dbo.Permit (RecordNumber)
	ON UPDATE NO ACTION ON DELETE NO ACTION;

/* Add Foreign Key: fk_ParentChild_Permit2 */
ALTER TABLE dbo.ParentChild ADD CONSTRAINT fk_ParentChild_Permit2
	FOREIGN KEY (ChildRecordNumber) REFERENCES dbo.Permit (RecordNumber)
	ON UPDATE NO ACTION ON DELETE NO ACTION;

/* Add Foreign Key: fk_WAP_ConsentsSites */
ALTER TABLE dbo.WAP ADD CONSTRAINT fk_WAP_ConsentsSites
	FOREIGN KEY (SiteID) REFERENCES dbo.ConsentsSites (SiteID)
	ON UPDATE NO ACTION ON DELETE NO ACTION;