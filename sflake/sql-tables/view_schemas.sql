CREATE OR REPLACE View GwAllocationSummary AS
SELECT
gwl."SpatialUnitId" as SpatialUnitId,
gwl."AllocationBlock" as AllocationBlock,
gwl."Name" as name,
gwa."AllocatedVolume" as AllocatedVolume,
gwa."NewAllocationInProgress" as NewAllocationInProgress,
gwl."AllocationLimit" as AllocationLimit,
iff(gwl."AllocationLimit" = 0, 0, (gwl."AllocationLimit" - gwa."AllocatedVolume")) as AllocationAvailable,
iff(gwl."AllocationLimit" = 0, 0, (gwa."AllocatedVolume"/gwl."AllocationLimit")*100)::Int as AllocatedPercentage,
gwl."Units" as units, gwl."Notes" as notes,
gwl."PlanName" AS PlanName,
gwl."PlanSection" AS PlanSection,
gwl."PlanTable" AS PlanTable
from "WATERDATAREPO"."Curated"."GwZoneLimits" as gwl
inner join "WATERDATAREPO"."Curated"."GwZoneAllocation" as gwa
on gwl."SpatialUnitId" = gwa."SpatialUnitId" and gwl."AllocationBlock" = gwa."AllocationBlock";

CREATE OR REPLACE View SwAllocationSummary AS
SELECT
swl."SpatialUnitId" as SpatialUnitId,
swl."Name" as name,
swl."AllocationBlock" as AllocationBlock,
CASE swl."Month"
    WHEN 7 THEN 'Jan'
    WHEN 8 THEN 'Feb'
    WHEN 9 THEN 'Mar'
    WHEN 10 THEN 'Apr'
    WHEN 11 THEN 'Map'
    WHEN 12 THEN 'Jun'
    WHEN 1 THEN 'Jul'
    WHEN 2 THEN 'Aug'
    WHEN 3 THEN 'Sep'
    WHEN 4 THEN 'Oct'
    WHEN 5 THEN 'Nov'
    WHEN 6 THEN 'Dec'
    ELSE 'Jul'
end AS Month,
swl."Month" AS MonthId,
swa."AllocatedRate" as AllocatedRate,
swa."NewAllocationInProgress" as NewAllocationInProgress,
swl."AllocationLimit" as AllocationLimit,
iff(swl."AllocationLimit" = 0, 0, (swl."AllocationLimit" - swa."AllocatedRate")) as AllocationAvailable,
iff(swl."AllocationLimit" = 0, 0, (swa."AllocatedRate"/swl."AllocationLimit")*100)::Int as AllocatedPercentage,
swl."Units" as units, swl."Notes" as notes,
swl."PlanName" AS PlanName,
swl."PlanSection" AS PlanSection,
swl."PlanTable" AS PlanTable
from "WATERDATAREPO"."Curated"."SwZoneLimits" as swl
inner join "WATERDATAREPO"."Curated"."SwZoneAllocation" as swa
on swl."SpatialUnitId" = swa."SpatialUnitId"
and swl."AllocationBlock" = swa."AllocationBlock"
and swl."Month" = swa."Month";

CREATE OR REPLACE VIEW ConsentDetails AS
SELECT
"RecordNumber" AS RecordNumber
, "HydroGroup" as hydrogroup
, "AllocationBlock" as allocationblock
, "Wap" as wap
, "SpatialUnitId" as spatialunitid
, "ConsentStatus" as consentstatus
, "FromDate"::date as fromdate
, "ToDate"::date as todate
, CASE "FromMonth"
    WHEN 7 THEN 'Jan'
    WHEN 8 THEN 'Feb'
    WHEN 9 THEN 'Mar'
    WHEN 10 THEN 'Apr'
    WHEN 11 THEN 'Map'
    WHEN 12 THEN 'Jun'
    WHEN 1 THEN 'Jul'
    WHEN 2 THEN 'Aug'
    WHEN 3 THEN 'Sep'
    WHEN 4 THEN 'Oct'
    WHEN 5 THEN 'Nov'
    WHEN 6 THEN 'Dec'
    ELSE 'Jul'
end AS FromMonth
, CASE "ToMonth"
    WHEN 7 THEN 'Jan'
    WHEN 8 THEN 'Feb'
    WHEN 9 THEN 'Mar'
    WHEN 10 THEN 'Apr'
    WHEN 11 THEN 'Map'
    WHEN 12 THEN 'Jun'
    WHEN 1 THEN 'Jul'
    WHEN 2 THEN 'Aug'
    WHEN 3 THEN 'Sep'
    WHEN 4 THEN 'Oct'
    WHEN 5 THEN 'Nov'
    WHEN 6 THEN 'Dec'
    ELSE 'Jun'
end AS ToMonth
, "AllocatedRate" as allocatedrate
, "AllocatedAnnualVolume" as allocatedannualvolume
, "EffectiveFromDate" as calculatedat
from "WATERDATAREPO"."Curated"."ConsentedAllocation"
WHERE consentstatus in ('Issued - Active', 'Issued - Inactive', 'Issued - s124 Continuance', 'Application in Process');

CREATE OR REPLACE View "PowerBiConsentsDetails" AS
SELECT
  ca."RecordNumber",
	ca."HydroGroup",
	ca."AllocationBlock",
	ca."Wap",
	ca."SpatialUnitId",
  sgw."SpatialUnitName",
	ca."Combined",
	ca."ConsentStatus",
	ca."FromDate",
	ca."ToDate",
	ca."FromMonth",
	ca."ToMonth",
	ca."AllocatedRate",
	ca."AllocatedAnnualVolume",
	ca."EffectiveFromDate"
from
(SELECT DISTINCT "SpatialUnitId" , "Name" as "SpatialUnitName"
FROM WATERDATAREPO."Curated"."GwZoneLimits") as sgw
inner join WATERDATAREPO."Curated"."ConsentedAllocation" as ca on sgw."SpatialUnitId" = ca."SpatialUnitId";
