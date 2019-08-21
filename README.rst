ECan water consents reporting tables
==================================

This git repository contains code necessary to populate/update the tables for the ECan water consents data.

Consenting Rules as they relate to water permits
-------------------------------------------------
Intro
~~~~~
There are lots of rules surrounding how we issue water consents and the associated conditions. This document will try to describe as much of the rules as possible for a system developer. Some of these rules WILL have some exceptions, but are not worth creating overly complex rules for a small handful of bad consents.

Basic concepts/entities
~~~~~~~~~~~~~~~~~~~~~~~
The fundamental entities of permits include the permit itself, the regulatory plan associated with area of the permit, the activity types permitted (e.g. use, take, divert, discharge), the allocation blocks used for accounting, sites/locations associated with the permits and activities (e.g. WAPs), and the conditions of the permit and activities (e.g. max rate, annual volume, use type).

Permit
~~~~~~
The permit at the top level (e.g. applies to all activities associated with it) have dates relating to when it was lodged, applicable, etc. It also contains the status of the permit (e.g. Issued - Active, Issued - Terminated), relationships to the parent permit, and other data associated with the entire permit.

Activities
~~~~~~~~~~
Water related activities include, takes, diverts, use, dam, and discharge. These are physical activities performed on one of two hydrologic features: Surface Water or Groundwater.

Sites
~~~~~
As all activities are physical, they are all performed at some geographic location. Sites in this context can be one or more points, lines, or polygons. For example, Takes are abstractions from wells which are represented as points, while the Use for irrigation would be applied to agricultural land represented by a polygon.

Allocation Blocks
~~~~~~~~~~~~~~~~~
The concept of allocation blocks only relate to Take activities. The goal of allocation blocks is to define abstraction limits for specific areas/rivers. Each permit with a Take activity has their Take accounted in the surface water and/or groundwater allocation blocks associated with the plan in the area where the water is taken. This assessment is performed when someone applies for a Take permit to determine if there is any more water available to be taken given the existing limits and accounting.
Allocation block limits come in the form of either a rate (as is generally for surface water) or an annual volume (as is generally for groundwater), but allocation blocks can potentially have both rates and annual volumes for both surface water and groundwater depending on the area/plan.

Specific consenting rules
~~~~~~~~~~~~~~~~~~~~~~~~~
The activities take, divert, use, and discharge must have a consented max rate > 0. There also tends to be a variety of volume conditions over a number of days that could be consented, but it is not required. Generally, a Take Groundwater activity will have a consented annual volume and will be the case going forward, but many of the old consents do not have this.

Each different activity should have a site/location of where this activity applies to. This is most explicit with the Takes and their associated Water Abstraction Points (WAPs). These are conceptually the point(s) where the water is taken from the hydrologic feature. ECan has given them coordinate namings like those of our monitoring wells even if they draw from surface water. Diverts have also been given the site type of WAP even though they probably should have a different name and they should more appropriately be lines representing the diversion route as a point or set of points do not adequately represent the location of a diversion.

Unfortunately, the activities Use, Dam, and Discharge do not have explicitly associated spatial locations. These should be added in the future and in addition to the points we should also allow lines and polygons to be associated with activities. This is especially important for Use irrigation activities to know the irrigated areas associated with the Use.

LowFlow Conditions
~~~~~~~~~~~~~~~~~~
Within and in addition to allocation blocks, lowflow conditions are assigned to permits that are counted in the surface water allocation blocks. These conditions are meant to ensure that rivers will have a minimum amount of flow regardless of the other permitted conditions and associated allocation blocks.

These lowflow conditions have trigger flows that require the Take activity to be reduced or cease. These trigger flows are generally defined by the associated plans for the rivers/SWAZs and allocation blocks, but can be defined uniquely for the permitted Take activity.

Going forward with our permitting, one permit should have one take for one SW allocation block. But in the past one permit could have multiple takes on multiple allocation blocks. This means that a single permit could have multiple sets of lowflow conditions if they were on multiple allocation blocks.

In general, a permit with a Take on a SW allocation block will have a single set of lowflow conditions on one SW or GW monitoring site. In the past, it was possible for people to have multiple sets of lowflow conditions on multiple SW or GW monitoring sites, but this should not be allowed going forward as the logic and relationships of how to handle those combinations are complicated and unnecessary.


Conceptual model
----------------------------------
in progress...

Physical model
----------------
A physical model was designed for an MS SQL database named ConsentsReporting. An `SQL script <https://github.com/Data-to-Knowledge/ConsentsReporting/blob/master/TableCreation.sql>`_ has been made to create the tables and relationships. A `database diagram <https://github.com/Data-to-Knowledge/ConsentsReporting/blob/master/diagrams/CR_data_model_v05.png>`_ has been made to illustrate the tables the relationships in dbeaver. This is the core model that is a representation of the conceptual model.

The source tables used in filling the core physical model is stored as a `yaml file <https://github.com/Data-to-Knowledge/ConsentsReporting/blob/master/parameters.yml>`_. The tables are all located within ECan's internal network.

The month numbers listed in the tables start from July due to the fact that most requests use the business (or water) year. So July is listed as month 1.

Filters to ensure the physical model is complete
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The python scripts to populate and update the core physical model can be found `here <https://github.com/Data-to-Knowledge/ConsentsReporting/blob/master/process_data.py>`_. Without going into detail, there are many filters in the scripts purely to ensure that the existing data is complete enough to fill the tables and relationships (e.g. there must be a FromDate attribute in the Permit table). A consented or allocated rate or volume of 0 has been converted to null as these are not correct.

Splitting the rates and volumes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Both the consented and allocated rates and volumes would need to be split according to their appropriate combo of consent number, activity/allocation block, and site. This is not always obvious from the source tables. For example, the consented rate (and volume) is stored against the consent number and activity, but not the site (AKA Wap). The site/Wap may have a specific rate, but it's not necessarily connected with the consented rate. To split it across all three entities, we have used the proportion ratio of the individual site/Wap to the total sites/Waps for the entire consent and this ratio is multiplied by the consented rate (or volume). This assumption is made for the consented and allocated rates and volumes when necessary. If there is only one site/Wap for the entire consent, then no proportioning is needed.

Water use types
~~~~~~~~~~~~~~~
Similar to the rates and volumes, the water use types (e.g. agriculture, water supply, etc.) are split by consent number and activity only in the source tables. Most of the time there is only one water use type, but is a significant number of cases there are several. Unlike rate and volumes, there is not a clear way to split these use types across one or more sites/Waps. Consequently, only one use type is selected from the source use types and prioritised according to the use_types_priorities parameter in the parameters.yml file. One use type is assigned to all Waps within the combo key of consent number and activity/allocation block.
