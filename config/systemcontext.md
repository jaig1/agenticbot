You're an expert at SQL. You will be given a user's natural language prompt

<user_prompt>Get me all the vehicles that are unshipped at my plant with associated status</user_prompt>

<sql schema>
---- This is a table schema to be used when a user prompts to generate SQL statements. The users will not expect you to return data, just the SQL queries
-- The queries will be executed on Google Cloud Big Query on the project ford-1c3ca485d9bfcbd60deceba4


CREATE TABLE IF NOT EXISTS uqm.pcm_assembly_plant_code
(
    vo_code                STRING NOT NULL,
    sales_code_description STRING,
    region                 STRING,
    access_ad_group        STRING,
    timezone               STRING,
    tz_code                STRING,
    dst_flag               STRING,
    lastupdatedby           STRING,
    lastupdatedon          DATETIME
) CLUSTER BY vo_code;


CREATE TABLE IF NOT EXISTS uqm.pcm_avs_vims
(
    vin                        STRING NOT NULL,
    avs_code                   STRING,
    avs_code_last_updated      STRING,
    yard_location              STRING,
    yard_location_last_updated STRING,
    order_type                 STRING,
    national_blend_code        INT64,
    national_blend_date        DATE,
    lastupdatedby               STRING,
    lastupdatedon              DATETIME
) cluster by vin;

CREATE TABLE IF NOT EXISTS uqm.pcm_campaign_detail
(
    campaign_id              STRING NOT NULL,
    serial_number            STRING NOT NULL,
    plant_id                 INT64  NOT NULL,
    campaign_description     STRING,
    campaign_check_text      STRING,
    campaign_type_text       STRING,
    inspection_time          INT64,
    campaign_sticker         STRING,
    campaign_type_id         INT64,
    campaign_state_id        STRING,
    campaign_start_date      DATETIME,
    campaign_closed_date     DATETIME,
    campaign_vin_status      STRING,
    campaign_good_sticker    STRING,
    campaign_bad_sticker     STRING,
    change_timestamp         DATETIME,
    gate_releaseable         STRING,
    good_timestamp           STRING,
    bad_timestamp            STRING,
    stop_ship_number         STRING,
    units_in_campaign        INT64,
    campaign_inspection_item STRING,
    return_unit_to_plant     STRING,
    lastupdatedby             STRING,
    lastupdatedon            DATETIME
) CLUSTER BY campaign_id, serial_number, plant_id;

CREATE TABLE IF NOT EXISTS uqm.pcm_campaign_sticker_lang
(
	plant                   STRING,
	plant_id                INT64,
	campaign_sticker_id     INT64,
	campaign_sticker_text   STRING,
	lastupdatedby   STRING,
	lastupdatedon   DATETIME
);


CREATE TABLE IF NOT EXISTS uqm.pcm_connected_vehicle_detail
(
	vin                             STRING,
	modemtimestamp_utc              DATETIME,
	modembundle_version             STRING,
	modem_mode                      STRING,
	gpstimestamp_utc                DATETIME,
	rrtire_pressure                 FLOAT64,
	rftire_pressure                 FLOAT64,
	lrtire_pressure                 FLOAT64,
	lftire_pressure                 FLOAT64,
	cvdc62_pwpcktq_d_stat_c         STRING,
	cvdc62_pwpck_d_stat_c           STRING,
	fuel_range                      FLOAT64,
	fuel_level_pc                   FLOAT64,
	engineoil_life_pc               INT64,
	enginecoolant_temp              INT64,
	battery_soc                     INT64,
	battery_voltage                 FLOAT64,
	dt                              DATETIME,
	lowfuel_flag                    STRING,
	lowoillife_flag                 STRING,
	lowbatteryvoltage_flag          STRING,
	gpsdataexists_flag              STRING,
	lowtirepressure_flag            STRING,
	tire_lf_flag                    STRING,
	tire_rf                         STRING,
	tire_lr_flag                    STRING,
	tire_rr_flag                    STRING,
	lowtire_pressure                STRING,
	longitude_decimal_degrees       BIGNUMERIC,
	latitude_decimal_degrees        BIGNUMERIC,
	rrtire_pressure_status          STRING,
	rftire_pressure_status          STRING,
	lrtire_pressure_status          STRING,
	lftire_pressure_status          STRING,
	payloadmetadata_version         STRING,
	odometermaster_value            INT64,
	velocity                        FLOAT64,
	message_flag                    INT64,
	message_name                    STRING,
	gpsdata_confidence              STRING,
	velocity_timestamp_utc          DATETIME,
	odometer_timestamp_utc          DATETIME,
	did_ign_cycle_cnt               STRING,
	did_ign_cycle_cnt_ts_utc        DATETIME,
	evbattery_range_val             FLOAT64,
	evbattery_range_timestamp_utc   DATETIME,
	authstat_val                    STRING,
	authstat_timestamp_utc          DATETIME,
	auth_type                       STRING,
	auth_type_timestamp_utc         DATETIME,
	auth_type_src                   STRING,
	ambient_air_temp                FLOAT64,
	ambient_air_temp_timestamp_utc  DATETIME,
	ambient_air_temp_src            STRING,
	selling_dlr_country             STRING,
	lv_battery_soc_ts_utc           DATETIME,
	traction_battery_soc_pc         FLOAT64,
	traction_battery_soc_pc_ts_utc  DATETIME,
  lastupdatedby                   STRING,
  lastupdatedon                   DATETIME
);


CREATE TABLE IF NOT EXISTS uqm.pcm_connected_vehicle_dtc_detail
(
	vin                      STRING,
    dt                       DATE,
    ecu_json_id              INT64,
    ecuid                    STRING,
    ecu_status               STRING,
    dtc_json_id              INT64,
    dtc_id                   STRING,
    dtc_status               STRING,
    dtc_additional_info      STRING,
    dtc_modem_timestamp_utc  DATETIME,
  	lastupdatedby      			 STRING,
  	lastupdatedon       		 DATETIME);


CREATE TABLE IF NOT EXISTS uqm.pcm_freight_verify_data
(
	vin                 STRING NOT NULL,
	yard_location       STRING,
	bay_location        STRING,
	reason_code         STRING,
	event_date          DATETIME,
  lastupdatedby       STRING,
  lastupdatedon       DATETIME
) CLUSTER BY vin;



CREATE TABLE IF NOT EXISTS uqm.pcm_geofence5
(
	label           STRING NOT NULL,
	plant_name      STRING,
	spatial_obj     GEOGRAPHY,
	lastupdatedby   STRING,
	lastupdatedon   DATETIME
) CLUSTER BY label;



CREATE TABLE IF NOT EXISTS uqm.pcm_navis_non_shipped
(
    vin                     STRING  NOT NULL,
    df0r48_veh_stat_c       STRING,
    assemblyplntcd          STRING,
    df0r48_load_s           DATETIME,
    model                   STRING,
    model_year              INT64,
    color                   STRING,
    vehicle_description     STRING,
    order_type              STRING,
    produceddate            DATETIME,
    releaseddate            DATETIME,
    shippeddate             DATETIME,
    laststatdate            DATETIME,
    buildevent              STRING,
    buildevent_desc         STRING, 
    plant                   STRING,
	lastupdatedby   				STRING,
	lastupdatedon   				DATETIME
		)
CLUSTER BY vin;



CREATE TABLE IF NOT EXISTS uqm.pcm_ota_status
(
	vin                 STRING NOT NULL,
	correlation_id      STRING NOT NULL,
	ecu_id              STRING NOT NULL,
	ecu_address         STRING NOT NULL,
	deployment_status   STRING,
	vin_status_code     STRING,
	vin_status_desc     STRING,
	vin_status_date     DATETIME,
	vin_status_time_ms  INT64,
	env                 STRING,
	country             STRING,
  lastupdatedby       STRING,
  lastupdatedon       DATETIME
) 
CLUSTER BY vin, correlation_id, ecu_id, ecu_address;



CREATE TABLE IF NOT EXISTS uqm.pcm_plant_unit_location
(
    qls_unit_id             INT64      NOT NULL,
    plant_id                INT64      NOT NULL,
    plant_unit_location_id  INT64,
    unit_pul_timestamp      DATETIME,
    unit_location_name      STRING,
    vin                     STRING,
    aisle_id                INT64,
    bay_id                  INT64,
    aisle_name              STRING,
  	lastupdatedby       STRING,
  	lastupdatedon       DATETIME
) CLUSTER BY qls_unit_id, plant_id;


CREATE TABLE IF NOT EXISTS uqm.pcm_plant_unit_location_aisle_lang
(
    plant_unit_location_id  INT64,
    plant_id                INT64,
    aisle_id                INT64,
    aisle_name              STRING,
    language_id             INT64,
    plant                   STRING,
  	lastupdatedby       STRING,
  	lastupdatedon       DATETIME
);


CREATE TABLE IF NOT EXISTS uqm.pcm_qls_unit(
	serial_number           STRING,
	plant_id                INT64 NOT NULL,
	qls_unit_id             INT64 NOT NULL,
	lastupdatedby   STRING,
	lastupdatedon   DATETIME
) CLUSTER BY plant_id, qls_unit_id;



CREATE TABLE IF NOT EXISTS uqm.pcm_run_settings(
	property             STRING,
	value                STRING,
    lastupdatedby        STRING,
    lastupdatedon        DATETIME
);


CREATE TABLE IF NOT EXISTS uqm.pcm_samis_non_shipped(
	vin                     STRING NOT NULL,
	df0r48_veh_stat_c       STRING,
	model                   STRING,
	vehicle_description     STRING,
	color                   STRING,
	assemblyplntcd          STRING,
	df0r48_load_s           DATETIME,
	model_year              INT64,
	order_type              STRING,
	plant                   STRING,
	lastupdatedby  				  STRING,
	lastupdatedon   				DATETIME
) CLUSTER BY vin;


CREATE TABLE IF NOT EXISTS uqm.pcm_shipping_pul(
	plant_id                INT64 NOT NULL,
	product_line_id         INT64 NOT NULL,
	shipping_pul_id         INT64 NOT NULL,
	plant                   STRING,
	shipping_pul_name       STRING,
	lastupdatedby   STRING,
	lastupdatedon   DATETIME
) CLUSTER BY plant_id, product_line_id, shipping_pul_id;


CREATE TABLE IF NOT EXISTS uqm.pcm_unit_chargeholdresult(
	vin                     STRING NOT NULL,
	becm_serial             STRING NOT NULL,
	result                  STRING,
	historical_result       STRING,
	cell_count              INT64,
	suspect_cell            STRING,
	manual_result           STRING,
	upload_ts_utc           DATETIME,
	lastupdatedby           STRING,
	lastupdatedon           DATETIME
) CLUSTER BY vin, becm_serial;



CREATE TABLE IF NOT EXISTS uqm.pcm_unit_concern(
    uc_id                         STRING     NOT NULL,
    unit_collection_pt_timestamp  DATETIME  NOT NULL,
    plant_id                      INT64,
    qls_unit_id                   INT64,
    unit_concern_state            STRING,
    evaluation_comment            STRING,
    inspection_item               STRING,
    uc_unit_concern               STRING,
    charged_department            STRING,
    vrt                           STRING,
    uc_vfg                        STRING,
    uc_ccc                        STRING,
    uc_ccc_desc                   STRING,
    plant                         STRING,
    lastupdatedon                 DATETIME,
    lastupdatedby                 STRING
)CLUSTER BY uc_id;



CREATE TABLE IF NOT EXISTS uqm.pcm_unit_concern_repair(
    uc_id                      STRING     NOT NULL,
    unit_repair_timestamp      DATETIME  NOT NULL,
    unit_repair_timestamp_s    INT64      NOT NULL,
    qls_unit_id                INT64,
    plant_id                   INT64,
    repair_state               STRING,
    repair_duration            STRING,
    repair_person_id           INT64,
    zone_id                    INT64,
    plant                      STRING,
    lastupdatedon              DATETIME,
    lastupdatedby              STRING
)CLUSTER BY uc_id;


CREATE TABLE IF NOT EXISTS uqm.pcm_unit_concern_undefined(
	uc_id                           STRING NOT NULL,
    qls_unit_id                     INT64,
	plant_id                        INT64,
	unit_collection_pt_timestamp    DATETIME,
	inspection_item                 STRING,
	uc_unit_concern                 STRING,
	unit_concern_state              STRING,
	evaluation_comment              STRING,
	plant                           STRING,
  lastupdatedby  						      STRING,
  lastupdatedon 					        DATETIME
)CLUSTER BY uc_id;


CREATE TABLE IF NOT EXISTS uqm.pcm_unit_master(
    vin                               STRING     NOT NULL,
    serial_number                     STRING,
    plant_id                          INT64,
    qls_unit_id                       INT64,
    rotation_job_number               STRING,
    model                             STRING,
    model_year                        INT64,
    vehicle_description               STRING,
    color                             STRING,
    produced_date                     DATETIME,
    released_date                     DATETIME,
    model_code                        STRING,
    product_line_id                   INT64,
    product_line_group_id             INT64,
    unit_id                           INT64,
    shipped_date                      DATETIME,
    vims_known_unit                   STRING,
    ship_status                       STRING,
    mandatory_cp_plant_unit_loc_id    INT64,
    route_code_prefix                 STRING,
    route_code                        STRING,
    special_ind                       STRING,
    ship_thru_ind                     STRING,
    emissions_ind                     STRING,
    shipping_spot                     STRING,
    shipping_ramp                     STRING,
    shipping_deck                     STRING,
    shipping_override_flag            STRING,
    batch_hold_start_time             DATETIME,
    shipping_user_id                  INT64,
    shipping_mode                     STRING,
    unit_status_code                  STRING,
    create_timestamp                  DATETIME,
    change_timestamp                  DATETIME,
    physical_vin                      STRING,
    df0r48_veh_stat_c                 STRING,
    produceddate                      STRING,
    assemblyplntcd                    STRING,
    df0r48_load_s                     DATETIME,
    modelyear                         INT64,
    plant                             STRING,
  	lastupdatedby      							  STRING,
  	lastupdatedon     							  DATETIME
	)
	 CLUSTER BY vin;


CREATE TABLE IF NOT EXISTS uqm.pcm_unit_missing_collectionpoint(
	vin                 STRING NOT NULL,
	serial_number       STRING NOT NULL,
	plant_id            INT64 NOT NULL,
	shipping_pul_id     INT64 NOT NULL,
	shipping_pul_name   STRING,
	mcp_ids             STRING,
	mcp_names           STRING,
	mcp_count           INT64,
	lastupdatedby       STRING,
	lastupdatedon  		DATETIME
) CLUSTER BY plant_id, vin, serial_number, shipping_pul_id;


CREATE TABLE IF NOT EXISTS uqm.pcm_unit_missing_plantunitlocation(
	vin                 STRING NOT NULL,
	serial_number       STRING NOT NULL,
	plant_id            INT64 NOT NULL,
	shipping_pul_id     INT64 NOT NULL,
	shipping_pul_name   STRING,
	mpul_ids            STRING,
	mpul_names          STRING,
	mpul_count          INT64,
	lastupdatedby       STRING,
	lastupdatedon		DATETIME
) CLUSTER BY plant_id, vin, serial_number, shipping_pul_id;


CREATE TABLE IF NOT EXISTS uqm.pcm_vin_geofence_match(
	vin                     STRING NOT NULL,
	lot_labels              STRING,
	distance_miles          FLOAT64,
	direction               STRING,
	distance_feet           FLOAT64,
	direction_vehicle       STRING,
	lastupdatedby  				  STRING,
	lastupdatedon  				  DATETIME

);



CREATE TABLE IF NOT EXISTS uqm.pcm_vmacs_color_description(
	plant_colour_code       STRING,
	description             STRING,
  lastupdatedby           STRING,
  lastupdatedon           DATETIME
);


CREATE TABLE IF NOT EXISTS uqm.pcm_vmacs_non_shipped(
    vin                   STRING,
    df0r48_veh_stat_c     STRING,
    model                 STRING,
    vehicle_description   STRING,
    color                 STRING,
    assemblyplntcd        STRING,
    df0r48_load_s         DATETIME,
    plant                 STRING,
    nsc_order_type        STRING,
    nsc_sale_type         STRING,
    global_sales_type     STRING,
    value                 STRING,
    cdv_description       STRING,
    lastupdatedby         STRING,
    lastupdatedon         DATETIME 
);

</sql schema>

Please return your response as a SQL SELECT statement without additional narrative

<sql_statement>

Here are some example queries
-- Generate a list of vehicles (vin) that are still in the plant inventory with their associated status information
-- Include avs codes from pcm_avs_vims, freight verify location data from pcm_freight_verify_data
-- Include navis status and vehicle details from pcm_navis_non_shipped, which contains vehicles produced in North American plants that the navis system things are still in the plant
-- Include vmacs status and vehicle details from pcm_vmacs_non_shipped, which contains vehicles produced in Europe and IMG region plants that the vmacs system things are still in the plant
-- Include samis status and vehicle details from pcm_samis_non_shipped, which contains vehicles produced in South America region plants that the samis system things are still in the plant
-- Include collection points that the vehicle has missed, there could be several for a single vehicle and multiple rows per vehicle
-- Include plant unit locations that the vehicle has missed, there could be several for a single vehicle and multiple rows per vehicle
-- Include the over the air (ota) update status for any ota updates sent to the vehicle
-- Get the proper descriptive assembly plant name from pcm_assembly_plant_code
-- Include the charge and hold test result in case the vehicle is a High Voltage battery electric vehicle
SELECT
    um.vin AS `VIN`,
    um.serial_number AS `SerialNumber`,
    um.qls_unit_id AS `qls_unit_id_um`,
    um.plant_id AS `plant_id_um`,
    um.rotation_job_number AS `RotationJob`,
    um.physical_vin AS `PhysicalVIN`,
    um.df0r48_veh_stat_c AS `NAVIS_VMACS_Status`, // Renamed to old format in the LOAD script
    um.df0r48_load_s AS `NAVIS_VMACS_Stat_Date`, // Renamed to old format in the LOAD script
    ns.shippeddate AS `NAVISShippedDate`,
    um.vehicle_description AS `VehicleDescription`,
    um.model_year AS `ModelYear`,
    um.plant AS `Plant`,
    COALESCE(ns.model, um.model, NULL) AS `Model`,
    um.model AS `VehicleLine`,
    um.color AS `Color`,
    CAST(um.produced_date AS DATE) AS `ProducedDay`,
    um.produced_date AS `Produced`,
    um.released_date AS `Released`,
    um.ship_status AS `ShippableStatus`,
    um.model_code,
    um.product_line_id,
    um.product_line_group_id,
    um.unit_id,
    um.shipped_date,
    um.vims_known_unit,
    um.mandatory_cp_plant_unit_loc_id,
    um.route_code_prefix,
    um.route_code,
    um.special_ind,
    um.ship_thru_ind,
    um.emissions_ind,
    um.shipping_spot,
    um.shipping_ramp,
    um.shipping_deck,
    um.shipping_override_flag,
    um.batch_hold_start_time,
    um.shipping_user_id,
    um.shipping_mode,
    um.unit_status_code,
    uv.avs_code AS `AVSCode`,
    uv.avs_code_last_updated AS `AVSCodelastUpdated`,
    uv.yard_location AS `LastKnownVIMSLoc`,
    uv.yard_location_last_updated AS `LastKnownVIMSLocTS`,
    uv.national_blend_code as national_blend_code,
    uv.national_blend_date  as national_blend_date,
    coalesce (ns.order_type,vs.cdv_description,uv.order_type,SNS.order_type, NULL) as `OrderType`,
    CASE
        WHEN UPPER(COALESCE(ns.order_type, vs.cdv_description, uv.order_type, NULL)) LIKE '%PLANNING%' OR 
        UPPER(COALESCE(ns.order_type, vs.cdv_description, uv.order_type, NULL)) LIKE '%COMPANY LEASE PLAN%' THEN 'Low'
        WHEN UPPER(COALESCE(ns.order_type, vs.cdv_description, uv.order_type, NULL)) LIKE '%RETAIL%' OR 
        UPPER(COALESCE(ns.order_type, vs.cdv_description, uv.order_type, NULL)) LIKE '%PLAN%' OR 
        UPPER(COALESCE(ns.order_type, vs.cdv_description, uv.order_type, NULL)) LIKE '%RETIREE%' THEN 'High'
        ELSE 'Low'
    END AS `Priority`,
    FVD.yard_location AS `FVLot`,
    FVD.bay_location AS `FVBay`,
    FVD.event_date AS `FVLocTS`,
    MCP.shipping_pul_name AS `ShippingPULName`,
    MCP.mcp_ids AS `MissingMandatoryCollectionPointIds`,
    MCP.mcp_names AS `MissingMandatoryCollectionPoints`,
    MCP.mcp_count AS `MissingMandatoryCollectionPointCount`,
    MPUL.mpul_ids AS `MissingMandatoryPlantUnitLocationIds`,
    MPUL.mpul_names AS `MissingMandatoryPlantUnitLocations`,
    MPUL.mpul_count AS `MissingMandatoryPlantUnitLocationCount`,
    ns.buildevent AS `BuildEventCode`,
    ns.buildevent_desc AS `BuildEventDesc`,
    ota.correlation_id AS `ota_correlation_id`,
    ota.ecu_id AS `ota_ecu`,
    ota.ecu_address AS `ota_ecu_Address`,
    ota.deployment_status AS `ota_deployment_status`,
    ota.vin_status_code AS `ota_vin_status_code`,
    ota.vin_status_desc AS `ota_vin_status_desc`,
    ota.vin_status_date AS `ota_vin_status_date`,
    LEFT(FORMAT_DATETIME('%Y-%m-%d %I:%M:%S %p', DATETIME(TIMESTAMP(ota.vin_status_date), APC.timezone)), 23) AS `ota_vin_status_date_local`,
    APC.region AS `Region`,
    CNH.becm_serial as becm_serial
    ,CNH.result      as cnh_result
    ,CNH.historical_result   as cnh_historical_result
    ,CNH.cell_count     as cnh_cell_count
    ,CNH.suspect_cell   as cnh_suspect_cells
    ,CNH.upload_ts_utc  as cnh_update_ts_utc
FROM
    `ford-1c3ca485d9bfcbd60deceba4.uqm.pcm_unit_master` AS um
LEFT OUTER JOIN
    `ford-1c3ca485d9bfcbd60deceba4.uqm.pcm_avs_vims` AS uv ON um.vin = uv.vin
LEFT OUTER JOIN
    `ford-1c3ca485d9bfcbd60deceba4.uqm.pcm_freight_verify_data` AS FVD ON um.vin = FVD.vin
LEFT OUTER JOIN
    `ford-1c3ca485d9bfcbd60deceba4.uqm.pcm_navis_non_shipped` AS ns ON um.vin = ns.vin
LEFT OUTER JOIN
    `ford-1c3ca485d9bfcbd60deceba4.uqm.pcm_vmacs_non_shipped` AS vs ON um.physical_vin = vs.vin
LEFT OUTER JOIN
    `ford-1c3ca485d9bfcbd60deceba4.uqm.pcm_unit_missing_collectionpoint` AS MCP ON um.plant_id = MCP.plant_id AND um.serial_number = MCP.serial_number
LEFT OUTER JOIN
    `ford-1c3ca485d9bfcbd60deceba4.uqm.pcm_unit_missing_plantunitlocation` AS MPUL ON um.plant_id = MPUL.plant_id AND um.serial_number = MPUL.serial_number
LEFT OUTER JOIN
    `ford-1c3ca485d9bfcbd60deceba4.uqm.pcm_samis_non_shipped` AS SNS ON um.physical_vin = SNS.vin
LEFT OUTER JOIN
    `ford-1c3ca485d9bfcbd60deceba4.uqm.pcm_ota_status` AS ota ON ota.vin = um.vin
LEFT JOIN
    `ford-1c3ca485d9bfcbd60deceba4.uqm.pcm_assembly_plant_code` AS APC ON APC.sales_code_description = um.plant
LEFT OUTER JOIN `ford-1c3ca485d9bfcbd60deceba4.uqm.pcm_unit_chargeholdresult` CNH on 
  CNH.vin = um.vin;
  
-- Get all quality concerns / defects filed on the vehicle (vin) as well as the repairs done on it
-- Include concerns that are undefined. 
SELECT 
    uc.plant_id as `plant_id_uc`
    ,uc.qls_unit_id as `qls_unit_id_uc`
    ,unit_collection_pt_timestamp as `UnitCollectionPointTS`
    ,unit_concern_state
    ,evaluation_comment as `EvaluationComment`
    ,inspection_item as `InspectionItem`
    ,Upper(uc_unit_concern) as `UnitConcern`
    ,charged_department as `ChargedDepartment`
    ,uc_id as `UC_ID`
    ,vrt as `vr_team`
    ,uc_vfg as `unit_concern_vfg`
    ,uc_ccc as `unit_concern_ccc`
    ,uc_ccc_desc as `unit_concern_ccc_desc`
    ,repair_timestamp as `RepairTimestamp`
    ,repair_state     as `RepairState`
    ,timetorepair     as `TimetoRepair`
From
(
SELECT 
    uc1.plant_id
    ,uc1.qls_unit_id
    ,uc1.unit_collection_pt_timestamp
    ,uc1.unit_concern_state
    ,uc1.evaluation_comment
    ,uc1.inspection_item
    ,uc1.uc_unit_concern
    ,uc1.charged_department
    ,uc1.uc_id
    ,uc1.vrt  
    ,uc1.uc_vfg
    ,uc1.uc_ccc
    ,uc1.uc_ccc_desc
    ,ucr.unit_repair_timestamp  as `repair_timestamp`
    ,ucr.repair_state  as `repair_state`
    //,dateDiff (minute, uc1.unit_collection_pt_timestamp, ucr.unit_repair_timestamp)  as `timetorepair`
    ,TIMESTAMP_DIFF(ucr.unit_repair_timestamp, uc1.unit_collection_pt_timestamp, MINUTE) AS `timetorepair`
FROM `ford-1c3ca485d9bfcbd60deceba4.uqm.pcm_unit_concern` uc1
LEFT JOIN `ford-1c3ca485d9bfcbd60deceba4.uqm.pcm_unit_concern_repair` ucr on 
ucr.uc_id = uc1.uc_id
Union All

SELECT 
    uc2.plant_id
	,uc2.qls_unit_id
    ,unit_collection_pt_timestamp
    ,unit_concern_state
    ,evaluation_comment
    ,inspection_item
    ,CONCAT ('UNDEFINED: ', Upper(evaluation_comment)) as `UnitConcern`
	,'UNKNOWN DEPT' as `ChargedDepartment`
	,CONCAT(uc2.plant_id, uc2.qls_unit_id, unit_collection_pt_timestamp, evaluation_comment) as `UC_ID`
    ,null as vrt
    ,null as uc_vfg
    ,null as uc_ccc
    ,null as uc_ccc_desc
	,null  as repair_timestamp
	,null as repair_state
	,null as timetorepair
FROM `ford-1c3ca485d9bfcbd60deceba4.uqm.pcm_unit_concern_undefined` uc2
) uc
;


-- Get the campaigns that the vehicle has been put on and the associated details
-- Each vehicle can be on multiple campaigns
-- Each campaign contains multiple vehicles
Select
       um.plant_id as `plant_id_cmp`
      ,um.vin as `vin_cmp`
      ,um.serial_number as `serial_number_cmp`
      ,inspection_time
      ,campaign_sticker As `CampaignSticker`
      ,campaign_type_id  
      ,campaign_state_id as `Status1`
      ,campaign_start_date
      ,campaign_closed_date as `Closed`
      ,uc.change_timestamp as `change_timestamp_cmp`
      ,gate_releaseable as `GateReleasable`
      ,return_unit_to_plant as `ReturnUnittoPlant`
      ,campaign_id as `CampaignID`
      ,campaign_description as `CampaignDescription`
      ,campaign_check_text as `CheckText`
      ,campaign_type_text as `CampaignType`
      ,cast (good_timestamp as datetime) as good_timestamp
      ,cast (bad_timestamp as datetime) as bad_timestamp
      ,campaign_vin_status as `CampaignVINStatus`
      ,campaign_good_sticker
      ,campaign_bad_sticker
      ,units_in_campaign
      ,stop_ship_number as `stop_ship_number`
      ,campaign_inspection_item
//       ,cast (uc.good_timestamp as datetime) as `campaign_good_timestamp`
//       ,cast (uc.bad_timestamp as datetime) as `campaign_bad_timestamp`
      
FROM `ford-1c3ca485d9bfcbd60deceba4.uqm.pcm_campaign_detail` uc
  INNER JOIN `ford-1c3ca485d9bfcbd60deceba4.uqm.pcm_unit_master` um
  ON uc.plant_id = um.plant_id
  AND uc.serial_number = um.serial_number;

-- Get connected vehicle (cv) details for individual vins that are still in inventory as stored in the unit_master table. 
-- Add in geo fencing information as well as a description of the plant name
-- Each row of this query will be a unique vin and only one row per vin is allowed
SELECT
    um.vin as vin_cv,
    FORMAT_DATETIME('%Y-%m-%d %I:%M:%S %p', modemtimestamp_utc) as `ModemTimestampUTC`,
    modembundle_version as `ModemBundleVersion`,
    modem_mode as `ModemMode`,
    message_flag as `MessageFlag`,
    message_name as `MessageName`,
    FORMAT_DATETIME('%Y-%m-%d %I:%M:%S %p',gpstimestamp_utc) as `GPSTimestampUTC`,
    FORMAT_DATETIME('%Y-%m-%d %I:%M:%S %p',gpstimestamp_utc)  as gpstimestamp_utc,
    gpstimestamp_utc   as gpstimestamp_utc_1,  //this is introduced to calculate max gps timestamp
    rrtire_pressure as `RRTirePressure`,
    rftire_pressure as `RFTirePressure`,
    lrtire_pressure as `LRTirePressure`,
    lftire_pressure as `LFTirePressure`,
    cvdc62_pwpcktq_d_stat_c,
    cvdc62_pwpck_d_stat_c,
    fuel_range as `FuelRange`,
    fuel_level_pc as `FuelLevelPC`,
    engineoil_life_pc as `EngineOilLifePC`,
    enginecoolant_temp as `EngineCoolantTemp`,
    battery_soc as `BatterySOC`,
    battery_voltage as `BatteryVoltage`,
    dt,
    lowfuel_flag as `LowFuelFlag`,
    lowoillife_flag as `LowOilLifeFlag`,
    lowbatteryvoltage_flag as `LowBatteryVoltageFlag`,
    gpsdataexists_flag as `GPSFlag`,
    lowtirepressure_flag as `LowTirePressureFlag`,
    tire_lf_flag as `TIRELFFLAG`,
    tire_rf as `TIRERF`,
    tire_lr_flag as `TIRELRFLAG`,
    tire_rr_flag as `TIRERRFLAG`,
    UPPER(`lowtire_pressure`) as `LowTirePressure`,
    longitude_decimal_degrees as `LongitudeDecimalDegrees`,
    latitude_decimal_degrees as `LatitudeDecimalDegrees`,
    rrtire_pressure_status as `RRTirePressureStatus`,
    rftire_pressure_status as `RFTirePressureStatus`,
    lrtire_pressure_status as `LRTirePressureStatus`,
    lftire_pressure_status as `LFTirePressureStatus`,
    payloadmetadata_version as `PayloadMetadataVersion`,
    odometermaster_value as `Mileage`,
    lot_labels as `GPSLot`,
    distance_miles,
    direction as `DirectiontoLot`,
    distance_feet as `VehicleDistanceftfromLot`,
    direction_vehicle as Direction,
    velocity as `Velocity`,
    gpsdata_confidence as `GPSConfidence`,
    FORMAT_DATETIME('%Y-%m-%d %I:%M:%S %p',velocity_timestamp_utc) as `VelocityTimestampUTC`,
    FORMAT_DATETIME('%Y-%m-%d %I:%M:%S %p',odometer_timestamp_utc) as `OdometerTimestampUTC`,
    did_ign_cycle_cnt as `EngineStartCount`,
    FORMAT_DATETIME('%Y-%m-%d %I:%M:%S %p',did_ign_cycle_cnt_ts_utc) as `EngineStartCountTSUTC`,
    evbattery_range_val as `EVBatteryRange`,
    FORMAT_DATETIME('%Y-%m-%d %I:%M:%S %p',evbattery_range_timestamp_utc) as `EVBatteryRangeTS`,
    authstat_val as `AuthorizationStatus`,
    FORMAT_DATETIME('%Y-%m-%d %I:%M:%S %p',authstat_timestamp_utc) as `AuthorizationStatusTSUTC`,
    auth_type as `AuthorizationType`,
    FORMAT_DATETIME('%Y-%m-%d %I:%M:%S %p',auth_type_timestamp_utc) as `AuthorizationTypeTSUTC`,
    ambient_air_temp as `AmbientAirTemp`,
    FORMAT_DATETIME('%Y-%m-%d %I:%M:%S %p', ambient_air_temp_timestamp_utc) as `AmbientAirTempTS`,
    selling_dlr_country as `SellingDealerCountry`,
    lv_battery_soc_ts_utc as `LV_Battery_SOC_TS_UTC`,
    traction_battery_soc_pc as `HV_Battery_SOC_PC`,
    FORMAT_DATETIME('%Y-%m-%d %I:%M:%S %p', traction_battery_soc_pc_ts_utc) as `HV_Battery_SOC_PC_TS_UTC`,
    LEFT(FORMAT_DATETIME('%Y-%m-%d %I:%M:%S %p', DATETIME(TIMESTAMP(LV_Battery_SOC_TS_UTC), APC.timezone)), 23) AS `LV_Battery_SOC_TS_Local`,
    LEFT(FORMAT_DATETIME('%Y-%m-%d %I:%M:%S %p', DATETIME(TIMESTAMP (gpstimestamp_utc), APC.timezone)), 23) AS `GPS_Timestamp_Local`
        
     
FROM
    `ford-1c3ca485d9bfcbd60deceba4.uqm.pcm_connected_vehicle_detail` AS cv
INNER JOIN
    `ford-1c3ca485d9bfcbd60deceba4.uqm.pcm_unit_master` AS um ON cv.vin = um.physical_vin
LEFT JOIN
    `ford-1c3ca485d9bfcbd60deceba4.uqm.pcm_vin_geofence_match` AS geo ON cv.vin = geo.vin
LEFT JOIN
    `ford-1c3ca485d9bfcbd60deceba4.uqm.pcm_assembly_plant_code` AS APC ON APC.sales_code_description = um.plant;
    
    
-- Get the DTCs that are reported by the vehicle through the connected vehicle data
SELECT 
      um.vin As `vin_cv_dtc`
      ,dtc_modem_timestamp_utc as `DTCModemTimestampUTC`
      ,ecu_json_id as `ecu_json_id`
      ,ecuid as `ECUID`
      ,ecu_status as `ECUStatus`
      ,dtc_id as `DTCID`
      ,dtc_status as `DTCStatus`
      ,dtc_additional_info as `DTCAddnlInfo`
  FROM `ford-1c3ca485d9bfcbd60deceba4.uqm.pcm_connected_vehicle_dtc_detail` cv1
  INNER JOIN `ford-1c3ca485d9bfcbd60deceba4.uqm.pcm_unit_master` um
  ON cv1.vin = um.physical_vin
 ;

