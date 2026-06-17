import os.path
from pathlib import Path
import llm_epanet
from epyt import epanet
from llm_epanet.utils.utils import get_networks_dir

networks_dir = get_networks_dir()

single_dummy_query = [
    {
        "id": "single_dummy_1",
        "prompt": "Run hydraulic simulation to answer what is the maximal pressure in the network",
        "command": "d.getComputedTimeSeries().Pressure.max()",
        "args": {},
        "expected": 133.88,
        "category": "hydraulics",
        "network": "Net1.inp"
    },
]


single_dummy_hard = [
    {
        "id": "hard_dummy_1",
        "prompt": "Are there nodes in the network where pressure exceeds the range of {min_p} to {max_p}. "
                    "Ignore the pressure in tanks and reservoirs",
        "command": "True if (d.getComputedTimeSeries().Pressure.max() > {max_p})"
                    "| (d.getComputedTimeSeries().Pressure.min() < {min_p}) else False",
        "args": {"min_p": 30, "max_p": 80},
        "expected": True,
        "category": "hydraulics",
        "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
    },
]

dummy_queries = [
        {
            "id": "dummy_1",
            "prompt": "Run hydraulic simulation to answer what is the maximal pressure in the network",
            "command": "d.getComputedTimeSeries().Pressure.max()",
            "args": {},
            "expected": 133.88,
            "category": "hydraulics",
            "network": "Net1.inp"
        },
        {
            "id": "dummy_2",
            "prompt": "How many pumps in the network?",
            "command": "d.getCounts().Pumps",
            "args": {},
            "expected": 1,
            "category": "static",
            "network": "Net1.inp"
        },
        {
            "id": "dummy_3",
            "prompt": "How many tanks in the network?",
            "command": "d.getCounts().Tanks",
            "args": {},
            "expected": 1,
            "category": "static",
            "network": "Net1.inp"
        },
        {
            "id": "dummy_4",
            "prompt": "What is the number of nodes in the network?",
            # another way to get node count is d.getCounts().Nodes
            "command": "d.getNodeCount()",
            "args": {},
            "expected": 11,
            "category": "static",
            "network": "Net1.inp"
        },
]

net1_queries = [
        {
            "id": "net1_1",
            "prompt": "How many pumps in the network?",
            "command": "d.getCounts().Pumps",
            "args": {},
            "expected": 1,
            "category": "static",
            "network": "Net1.inp"
        },
        {
            "id": "net1_2",
            "prompt": "How many tanks in the network?",
            "command": "d.getCounts().Tanks",
            "args": {},
            "expected": 1,
            "category": "static",
            "network": "Net1.inp"
        },
        {
            "id": "net1_3",
            "prompt": "What is the number of nodes in the network?",
            # another way to get node count is d.getCounts().Nodes
            "command": "d.getNodeCount()",
            "args": {},
            "expected": 11,
            "category": "static",
            "network": "Net1.inp"
        },
        {
            "id": "net1_4",
            "prompt": "What is the elevation at the node with ID {element_name}",
            # In this command we don't need to subtract 1 from the index
            # because in getNodeElevations the EPyT handle the indexes and get the value directly
            # the returned object is a float of the elevation and not a numpy array we need to parse
            "command": "d.getNodeElevations(d.getNodeIndex('{element_name}'))",
            "args": {"element_name": '12'},
            "expected": 700.0,
            "category": "static",
            "network": "Net1.inp"
        },
        {
            "id": "net1_5",
            "prompt": "What is the average network elevation?",
            "command": "d.getNodeElevations().mean()",
            "args": {},
            "expected": 723.6363636363636,
            "category": "static",
            "network": "Net1.inp"
        },
        {
            "id": "net1_6",
            "prompt": "Run hydraulic simulation to answer what is the pressure at node {element_name} at hour {t}",
            # Index - 1 because EPANET indexes starts from 1
            # the returned object is numpy array - indexes starts from 0
            "command": "d.getComputedTimeSeries().{param}[{t}, d.getNodeIndex('{element_name}')-1]",
            "args": {"param": "Pressure", "t": 5, "element_name": '32'},
            "expected": 112.37,
            "category": "hydraulics",
            "network": "Net1.inp"
        },
        {
            "id": "net1_7",
            "prompt": "Run hydraulic simulation to answer what is the level at tank with ID {element_name} at time {t}",
            # Index - 1 because EPANET indexes starts from 1
            # the returned object is numpy array - indexes starts from 0
            "command": "d.getComputedTimeSeries().{param}[{t},"
                       "d.getNodeTankIndex(d.getNodeTankNameID().index('{element_name}'))-1]",
            "args": {"param": "Pressure", "t": 5, "element_name": '2'},
            "expected": 56.88469314575195,
            "category": "hydraulics",
            "network": "Net1.inp"
        },
        {
            "id": "net1_8",
            "prompt": "Run hydraulic simulation to answer what is the overall demand in the network across all consumers and all time steps",
            "command": "d.getComputedTimeSeries().Demand[:, :-(d.getNodeReservoirCount()+d.getNodeTankCount())].sum()",
            "args": {},
            "expected": 27500,  # 29480 if using getComputedHydraulicTimeSeries instead of getComputedTimeSeries
            "category": "hydraulics",
            "network": "Net1.inp"
            # note: two run simulation functions of EPyT returns two different answers, both will be considered as true
        },
        {
            "id": "net1_9",
            "prompt": "Run hydraulic simulation to answer what is the maximal pressure in the network",
            "command": "d.getComputedTimeSeries().Pressure.max()",
            "args": {},
            "expected": 133.88,
            "category": "hydraulics",
            "network": "Net1.inp"
        },
        {
            "id": "net1_10",
            "prompt": "Run hydraulic simulation to answer in which node ID the maximal pressure is obtained",
            "command": "d.getNodeNameID(d.getComputedTimeSeries().Pressure.max(axis=0).argmax()+1)",
            "args": {},
            "expected": "10",
            "category": "hydraulics",
            "network": "Net1.inp"
        },
        {
            "id": "net1_11",
            "prompt": "Run hydraulic simulation to answer when is the maximal pressure obtained",
            "command": "d.getComputedTimeSeries().Pressure.max(axis=1).argmax()",
            "args": {},
            "expected": 12,
            "category": "hydraulics",
            "network": "Net1.inp"
        },
        {
            "id": "net1_12",
            "prompt": "Run hydraulic simulation to answer if there are nodes in the network where pressure exceeds "
                      "the range of {min_p} to {max_p}. "
                      "Ignore pressure in tanks and reservoirs",
            "command": "True if (d.getComputedTimeSeries().Pressure.max() > {max_p})"
                       "| (d.getComputedTimeSeries().Pressure.min() < {min_p}) else False",
            "args": {"min_p": 30, "max_p": 80},
            "expected": True,
            "category": "hydraulics",
            "network": "Net1.inp"
        },
        {
            "id": "net1_13",
            "prompt": "What is the total energy consumption across all time steps",
            # Energy is returned for all links, we need to select only pumps columns in the returned array
            "command": "d.getComputedHydraulicTimeSeries().Energy[:, [_ - 1 for _ in d.getLinkPumpIndex()]].sum()",
            "args": {},
            "expected": 1538.634750366211,
            "category": "hydraulics",
            "network": "Net1.inp"
        },
        {
            "id": "net1_14",
            "prompt": "What is the max head loss of pipe 11? "
                      "You can use the HeadLoss parameter of EPyT",
            "command": "d.getComputedTimeSeries().HeadLoss[:, d.getLinkIndex('11')-1].max()",
            "args": {},
            "expected": 3.210900068283081,
            "category": "hydraulics",
            "network": "Net1.inp"
        },
        {
            "id": "net1_15",
            "prompt": "What is the average pump flow along the simulation?",
            "command": "d.getComputedTimeSeries().Flow[:, d.getLinkIndex('9')-1].mean()",
            "args": {},
            "expected": 1094.25908203125,
            "category": "hydraulics",
            "network": "Net1.inp"
        },
        {
            "id": "net1_16",
            "prompt": "Run a quality simulation to answer what is the maximal chlorine concentration at node {element_name}",
            "command": "d.getComputedQualityTimeSeries().NodeQuality[:, d.getNodeIndex('{element_name}')-1].max()",
            "args": {"element_name": "12"},
            "expected": 0.7950194478034973,
            "category": "quality",
            "network": "Net1.inp"
        },
        {
            "id": "net1_17",
            "prompt": "Run a quality simulation to answer what is the maximal chlorine concentration at node "
                      "{element_name}",
            "command": "d.getComputedQualityTimeSeries().NodeQuality[:, d.getNodeIndex('{element_name}')-1].max()",
            "args": {"element_name": "31"},
            "expected": 0.583783745765686,
            "category": "quality",
            "network": "Net1.inp"
        },
        {
            "id": "net1_18",
            "prompt": "Run a quality simulation to answer what is the average chlorine concentration across all nodes"
                      "and time steps",
            "command": "d.getComputedQualityTimeSeries().NodeQuality.mean()",
            "args": {},
            "expected": 0.6078808778541274,
            "category": "quality",
            "network": "Net1.inp"
        },
        {
            "id": "net1_19",
            "prompt": "What will be the min pressure if all consumers consume 10% above the base demand? "
                      "Ignore the pressure in tanks and reservoirs "
                      "To get the base demands of all nodes use: d.getNodeBaseDemands()[1].",
            "command": "demands = d.getNodeBaseDemands()[1]"
                       "demands_new = [i * 1.1 for i in demands]"
                       "d.setNodeBaseDemands(demands_new)"
                       "d.getComputedTimeSeries()[:, :-(d.getNodeReservoirCount() + d.getNodeTankCount())].min()",
            "args": {},
            "expected": 104.67680358886719,
            "category": "hydraulics-scenarios",
            "network": "Net1.inp"
        },
        {
            "id": "net1_20",
            "prompt": "What is the average pressure in the network if all consumers consume 95% of the base demand? "
                      "Ignore the pressure in tanks and reservoirs "
                      "To get the base demands of all nodes use: d.getNodeBaseDemands()[1].",
            "command": "demands = d.getNodeBaseDemands()[1]"
                       "demands_new = [i * 0.95 for i in demands]"
                       "d.setNodeBaseDemands(demands_new)"
                       "d.getComputedTimeSeries().Pressure[:, :-(d.getNodeReservoirCount() + d.getNodeTankCount())].mean()",
            "args": {},
            "expected": 119.47761511908637,
            "category": "hydraulics-scenarios",
            "network": "Net1.inp"
        },
        {
            "id": "net1_21",
            "prompt": "What will be the max head loss of pipe with ID 11 if replacing its diameter to 16? "
                      "You can use the HeadLoss parameter of EPyT",
            "command": "d.setLinkDiameter(d.getLinkIndex('11'), 16)"
                       "d.getComputedTimeSeries().HeadLoss[:, d.getLinkIndex('11')-1].max()",
            "args": {},
            "expected": 1.951367974281311,
            "category": "hydraulics-scenarios",
            "network": "Net1.inp"
        }
    ]


net3_queries = [
        {
            "id": "net3_1",
            "prompt": "How many pumps in the network?",
            "command": "d.getCounts().Pumps",
            "args": {},
            "expected": 2,
            "category": "static",
            "network": "Net3.inp"
        },
        {
            "id": "net3_2",
            "prompt": "How many tanks in the network?",
            "command": "d.getCounts().Tanks",
            "args": {},
            "expected": 3,
            "category": "static",
            "network": "Net3.inp"
        },
        {
            "id": "net3_3",
            "prompt": "What is the number of nodes in the network?",
            # another way to get node count is d.getCounts().Nodes
            "command": "d.getNodeCount()",
            "args": {},
            "expected": 97,
            "category": "static",
            "network": "Net3.inp"
        },
        {
            "id": "net3_4",
            "prompt": "What is the elevation at node ID {element_name}",
            # In this command we don't need to subtract 1 from the index
            # because in getNodeElevations the EPyT handle the indexes and get the value directly
            # the returned object is a float of the elevation and not a numpy array we need to parse
            "command": "d.getNodeElevations(d.getNodeIndex('{element_name}'))",
            "args": {"element_name": '267'},
            "expected": 21.0,
            "category": "static",
            "network": "Net3.inp"
        },
        {
            "id": "net3_5",
            "prompt": "What is the average network elevation?",
            "command": "d.getNodeElevations().mean()",
            "args": {},
            "expected": 24.722680255079393,
            "category": "static",
            "network": "Net3.inp"
        },
        {
            "id": "net3_6",
            "prompt": "Run hydraulic simulation to answer what is the pressure at node ID {element_name} at hour {t}",
            # Index minus 1 because EPANET indexes starts from 1
            # the returned object is numpy array - indexes starts from 0
            "command": "d.getComputedHydraulicTimeSeries().{param}[{t}, d.getNodeIndex('{element_name}')-1]",
            "args": {"param": "Pressure", "t": 5, "element_name": '35'},
            "expected": 60.68,
            "category": "hydraulics",
            "network": "Net3.inp"
        },
        {
            "id": "net3_7",
            "prompt": "Run hydraulic simulation to answer what is the level of tank ID {element_name} at time {t}",
            # Index - 1 because EPANET indexes starts from 1
            # the returned object is numpy array - indexes starts from 0
            "command": "d.getComputedTimeSeries_ENepanet().Pressure[{t},"
                       "[d.getNodeTankIndex()[i] for i, x in enumerate(d.getNodeTankNameID())"
                       "if x == '{element_name}'][0] - 1]",
            "args": {"t": 5, "element_name": '2'},
            "expected": 10.31,
            "category": "hydraulics",
            "network": "Net3.inp"
        },
        {
            "id": "net3_8",
            "prompt": "What is the overall demand in the network across all consumers and all time steps",
            "command": "d.getComputedTimeSeries().Demand[:, :-(d.getNodeReservoirCount()+d.getNodeTankCount())].sum()",
            "args": {},
            "expected": 273524.45144844055,
            "category": "hydraulics",
            "network": "Net3.inp"
        },
        {
            "id": "net3_9",
            "prompt": "What is the maximal pressure in the network",
            "command": "d.getComputedTimeSeries().Pressure.max()",
            "args": {},
            "expected": 132.70094299316406,
            "category": "hydraulics",
            "network": "Net3.inp"
        },
        {
            "id": "net3_10",
            "prompt": "In which node ID the maximal pressure is obtained",
            "command": "d.getNodeNameID(d.getComputedTimeSeries().Pressure.max(axis=0).argmax()+1)",
            "args": {},
            "expected": "601",
            "category": "hydraulics",
            "network": "Net3.inp"
        },
        {
            "id": "net3_11",
            "prompt": "At what time (in hours) is the maximal pressure obtained",
            "command": "d.getComputedTimeSeries().Pressure.max(axis=1).argmax()",
            "args": {},
            "expected": 4,
            "category": "hydraulics",
            "network": "Net3.inp"
        },
        {
            "id": "net3_12",
            "prompt": "Are there nodes in the network where pressure exceeds the range of {min_p} to {max_p}. "
                      "Ignore the pressure in tanks and reservoirs",
            "command": "True if (d.getComputedTimeSeries().Pressure.max() > {max_p})"
                       "| (d.getComputedTimeSeries().Pressure.min() < {min_p}) else False",
            "args": {"min_p": 30, "max_p": 80},
            "expected": True,
            "category": "hydraulics",
            "network": "Net3.inp"
        },
        {
            "id": "net3_13",
            "prompt": "What is the energy consumption by pumps across all time steps? Note that only pump energy is asked and not all links",
            # Energy is returned for all links, we need to select only pumps columns in the returned array
            "command": "d.getComputedHydraulicTimeSeries().Energy[:, [_ - 1 for _ in d.getLinkPumpIndex()]].sum()",
            "args": {},
            "expected": 3715.3819541931152,
            "category": "hydraulics",
            "network": "Net3.inp"
        },
        {
            "id": "net3_14",
            "prompt": "What will be the total demand when all consumers consumes 10% more than the nominal",
            "command": "d.getComputedTimeSeries_ENepanet().Demand[:, :-(d.getNodeReservoirCount()+d.getNodeTankCount())].sum() * 1.1",
            "args": {},
            "expected": 300876.8965932846,
            "category": "hydraulics-scenarios",
            "network": "Net3.inp"
        },
        {
            "id": "net3_15",
            # 1) Multi line command - WILL NOT WORK ON 'execute_and_assert'
            # 2) This function changes the network configuration - increase demands by 10%
            #    to reset the network to its base state we need to load it again: d.epanet(<inp_path>)
            "prompt": "What will be the max pressure if all consumers consumes 10% above the nominal",
            "command": "demands = d.getNodeBaseDemands()[1]"
                       "demands_new = [i * 1.1 for i in demands]"
                       "d.setNodeBaseDemands(demands_new)"
                       "d.getComputedTimeSeries().Pressure.max()",
            "args": {},
            "expected": 132.34275817871094,
            "category": "hydraulics-scenarios",
            "network": "Net3.inp"
        },
        {
            "id": "net3_16",
            # 1) Multi line command - WILL NOT WORK ON 'execute_and_assert'
            # 2) This function changes the network configuration - increase demands by 10%
            #    to reset the network to its base state we need to load it again: d.epanet(<inp_path>)
            "prompt": "What will be the min pressure if all consumers consumes 10% above the nominal. "
                      "Ignore the pressure in tanks and reservoirs",
            "command": "demands = d.getNodeBaseDemands()[1]"
                       "demands_new = [i * 1.1 for i in demands]"
                       "d.setNodeBaseDemands(demands_new)"
                       "d.getComputedTimeSeries().Pressure.min()",
            "args": {},
            "expected": -0.9042598605155945,
            "category": "hydraulics-scenarios",
            "network": "Net3.inp"
        },
        {
            "id": "net3_17",
            # 1) Multi line command - WILL NOT WORK ON 'execute_and_assert'
            # 2) This function changes the network configuration
            #    to reset the network to its base state we need to load it again: d.epanet(<inp_path>)
            "prompt": "What will be the max pressure if pipe {element_name} is closed?",
            "command": "d.setLinkInitialStatus(d.getLinkIndex('{element_name}'), 0)"
                       "d.getComputedTimeSeries().Pressure.max()",
            "args": {'element_name': '173'},
            "expected": 162.8256072998047,
            "category": "hydraulics-scenarios",
            "network": "Net3.inp"
        },
        {
            "id": "net3_18",
            # 1) Multi line command - WILL NOT WORK ON 'execute_and_assert'
            # 2) This function changes the network configuration
            #    to reset the network to its base state we need to load it again: d.epanet(<inp_path>)
            "prompt": "What will be the min pressure if pipe {element_name} is closed? "
                      "Ignore the pressure in tanks and reservoirs",
            "command": "d.setLinkInitialStatus(d.getLinkIndex('{element_name}'), 0)"
                       "d.getComputedTimeSeries().Pressure.min()",
            "args": {'element_name': '173'},
            "expected": -12.186866760253906,
            "category": "hydraulics-scenarios",
            "network": "Net3.inp"
        },
        {
            "id": "net3_19",
            # 1) Multi line command - WILL NOT WORK ON 'execute_and_assert'
            # 2) This function changes the network configuration
            #    to reset the network to its base state we need to load it again: d.epanet(<inp_path>)
            "prompt": "In which node ID the min pressure is obtained in case that pipe ID {element_name} is closed? "
                      "Ignore the pressure in tanks and reservoirs",
            "command": "d.setLinkInitialStatus(d.getLinkIndex('{element_name}'), 0)"
                       "d.getNodeNameID(d.getComputedTimeSeries().Pressure.min(axis=0).argmin()+1)",
            "args": {'element_name': '173'},
            "expected": '10',
            "category": "hydraulics-scenarios",
            "network": "Net3.inp"
        },
        {
            "id": "net3_20",
            "prompt": "What is the average portion of water from the lake source in tank ID {element_name}?"
                      "Please note that water quality simulations starts with an initial condition"
                      "of zero water quality in all pipes.",
            "command": "d.getComputedQualityTimeSeries().NodeQuality[:, d.getNodeIndex('1')-1].mean()",
            "args": {"element_name": '1'},
            "expected": 5.9331222486545645,
            "category": "quality",  # Net3 file quality is set to trace on Lake source
            "network": "Net3.inp"
        },
        {
            "id": "net3_21",
            "prompt": "What is the average portion of water from the lake source in tank ID {element_name}?"
                      "Please note that water quality simulations starts with an initial condition"
                      "of zero water quality in all pipes.",
            "command": "d.getComputedQualityTimeSeries().NodeQuality[:, d.getNodeIndex('2')-1].mean()",
            "args": {"element_name": '2'},
            "expected": 0.030088421836746985,
            "category": "quality",    # Net3 file quality is set to trace on Lake source
            "network": "Net3.inp"
        },
        ]


l_town_queries = [
        {
            "id": "l_town_1",
            "prompt": "How many junctions in the network?",
            "command": "d.getCounts().Nodes",
            "args": {},
            "expected": 782,
            "category": "static",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
        },
        {
            "id": "l_town_2",
            "prompt": "How many pipes in the network?",
            "command": "d.getCounts().Tanks",
            "args": {},
            "expected": 905,
            "category": "static",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
        },
        {
            "id": "l_town_3",
            "prompt": "How many pumps and valves are in the network?",
            # another way to get node count is d.getCounts().Nodes
            "command": "d.getCounts().Pumps + d.getCounts().Valves",
            "args": {},
            "expected": 4,
            "category": "static",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
        },
        {
            "id": "l_town_4",
            "prompt": "What is the elevation at node ID {element_name}",
            # In this command we don't need to subtract 1 from the index
            # because in getNodeElevations the EPyT handles the indexes and gets the value directly
            # the returned object is a float of the elevation and not a numpy array we need to parse
            "command": "d.getNodeElevations(d.getNodeIndex('{element_name}'))",
            "args": {"element_name": 'n469'},
            "expected": 26.999500274658203,
            "category": "static",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
        },
        {
            "id": "l_town_5",
            "prompt": "What is the average network elevation?",
            "command": "d.getNodeElevations().mean()",
            "args": {},
            "expected": 30.25572835472739,
            "category": "static",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
        },
        {
            "id": "l_town_6",
            "prompt": "Run hydraulic simulation to answer what is the maximal flow of valve ID {element_name}",
            # Index minus 1 because EPANET indexes start from 1
            # the returned object is numpy array - indexes start from 0
            "command": "d.getComputedTimeSeries().Flow[:, d.getLinkIndex('PRV-3')-1].max()",
            "args": {"element_name": 'PRV-3'},
            "expected": 10.778778076171875,
            "category": "hydraulics",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
        },
        {
            "id": "l_town_7",
            "prompt": "Run hydraulic simulation to answer what is the flow of valve ID {element_name} at time {t} hour",
            "command": "t_idx = {t} * (3600 // d.getTimeReportingStep())"
                       "d.getComputedTimeSeries().Flow[t_idx, d.getLinkIndex('PRV-3')-1].max()",
            "args": {"element_name": 'PRV-3', 't': 6},
            "expected": 4.95993137359619,  # # 4.860877990722656 if using getComputedHydraulicTimeSeries instead of getComputedTimeSeries
            "category": "hydraulics",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
            # note: two run simulation functions of EPyT returns two different answers, both will be considered as true
        },
        {
            "id": "l_town_8",
            "prompt": "Run hydraulic simulation to answer what is the average pressure in the network",
            "command": "d.getComputedHydraulicTimeSeries().Pressure.mean()",
            "args": {"element_name": '2'},
            "expected": 46.10948177450992,
            "category": "hydraulics",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
        },
        {
            "id": "l_town_9",
            "prompt": "What is the overall demand in the network across all consumers and all time steps",
            "command": "d.getComputedTimeSeries_ENepanet().Demand[:, :-(d.getNodeReservoirCount()+d.getNodeTankCount())].sum()",
            "args": {},
            "expected": 356174.14771508286,
            "category": "hydraulics",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
        },
        {
            "id": "l_town_10",
            "prompt": "What is the maximal pressure in the network",
            "command": "d.getComputedTimeSeries().Pressure.max()",
            "args": {},
            "expected": 73.98970031738281,
            "category": "hydraulics",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
        },
        {
            "id": "l_town_11",
            "prompt": "In which node ID the maximal pressure is obtained",
            "command": "d.getNodeNameID(d.getComputedTimeSeries().Pressure.max(axis=0).argmax()+1)",
            "args": {},
            "expected": "n336",
            "category": "hydraulics",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
        },
        {
            "id": "l_town_12",
            "prompt": "When in hours is the maximal pressure obtained",
            "command": "d.getComputedTimeSeries().Pressure.max(axis=1).argmax()",
            "args": {},
            "expected": 4.416666667,
            "category": "hydraulics",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
        },
        {
            "id": "l_town_13",
            "prompt": "Find the IDs of the 5 links where the absolute max flow rates are the largest in the network",
            "command": "[d.getLinkNameID(_ + 1) for _ in np.argsort(np.abs(d.getComputedTimeSeries().Flow)"
                       ".max(axis=0))[-5:]]",
            "args": {},
            "expected": ['PRV-1', 'p227', 'p110', 'PRV-2', 'p235'],
            "category": "hydraulics",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
        },
        {
            "id": "l_town_14",
            "prompt": "Are there nodes in the network where pressure exceeds the range of {min_p} to {max_p}. "
                      "Ignore the pressure in tanks and reservoirs",
            "command": "True if (d.getComputedTimeSeries().Pressure.max() > {max_p})"
                       "| (d.getComputedTimeSeries().Pressure.min() < {min_p}) else False",
            "args": {"min_p": 30, "max_p": 80},
            "expected": True,
            "category": "hydraulics",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
        },
        {
            "id": "l_town_15",
            # 1) Multi line command - WILL NOT WORK ON 'execute_and_assert'
            # 2) This function changes the network configuration - increase demands by 10%
            #    to reset the network to its base state we need to load it again: d.epanet(<inp_path>)
            "prompt": "What will be the max pressure if all consumers consumes 10% above the base demand",
            "command": "demands = d.getNodeBaseDemands()[1]"
                       "demands_new = [i * 1.1 for i in demands]"
                       "d.setNodeBaseDemands(demands_new)"
                       "d.getComputedTimeSeries().Pressure.max()",
            "args": {},
            "expected": 73.98918151855469,
            "category": "hydraulics-scenarios",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
        },
        {
            "id": "l_town_16",
            # 1) Multi line command - WILL NOT WORK ON 'execute_and_assert'
            # 2) This function changes the network configuration - increase demands by 10%
            #    to reset the network to its base state we need to load it again: d.epanet(<inp_path>)
            "prompt": "What will be the average pressure in the network if all consumers consumes 10% above the base demand",
            "command": "demands = d.getNodeBaseDemands()[1]"
                       "demands_new = [i * 1.1 for i in demands]"
                       "d.setNodeBaseDemands(demands_new)"
                       "d.getComputedTimeSeries().Pressure[:, :-(d.getNodeReservoirCount() + d.getNodeTankCount())].mean()",
            "args": {},
            "expected": 46.20746637654507,  # 46.0348625758192 if not ignoring tanks and reservoirs
            "category": "hydraulics-scenarios",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
            # note: the query does not explicitly ask to ignore pressure at tanks and reservoirs although it is
            # reasonable to do so
            # The expected answer does ignore them, however both answers considered as correct
        },
        {
            "id": "l_town_17",
            # 1) Multi line command - WILL NOT WORK ON 'execute_and_assert'
            # 2) This function changes the network configuration - increase demands by 10%
            #    to reset the network to its base state we need to load it again: d.epanet(<inp_path>)
            "prompt": "What will be the max flow if all consumers consumes 10% above the base demand",
            "command": "demands = d.getNodeBaseDemands()[1]"
                       "demands_new = [i * 1.1 for i in demands]"
                       "d.setNodeBaseDemands(demands_new)"
                       "d.getComputedTimeSeries().Flow.max()",
            "args": {},
            "expected": 130.09222412109375,
            "category": "hydraulics-scenarios",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
        },
        {
            "id": "l_town_18",
            # 1) Multi line command - WILL NOT WORK ON 'execute_and_assert'
            # 2) This function changes the network configuration
            #    to reset the network to its base state we need to load it again: d.epanet(<inp_path>)
            "prompt": "What will be the min pressure at junctions (not including tanks and reservoirs) if pipe ID "
                      "{element_name} is closed? ",
            "command": "d.setLinkInitialStatus(d.getLinkIndex('{element_name}'), 0)"
                       "d.getComputedTimeSeries().Pressure[:, [_ for _ in range(d.getNodeJunctionCount())]].min()",
            "args": {'element_name': 'p182'},
            "expected": 24.810707092285156,
            "category": "hydraulics-scenarios",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
        },
        {
            "id": "l_town_19",
            # 1) Multi line command - WILL NOT WORK ON 'execute_and_assert'
            # 2) This function changes the network configuration
            #    to reset the network to its base state we need to load it again: d.epanet(<inp_path>)
            "prompt": "In which node ID the min pressure is obtained in case that pipe ID {element_name} is closed?"
                      "The question is about junctions only, not including tanks and reservoirs",
            "command": "d.setLinkInitialStatus(d.getLinkIndex('{element_name}'), 0)"
                       "d.getNodeJunctionNameID(d.getComputedTimeSeries().Pressure"
                       "[:, [_ for _ in range(d.getNodeJunctionCount())]].min(axis=0).argmin()+1)",
            "args": {'element_name': 'p182'},
            "expected": 'n22',
            "category": "hydraulics-scenarios",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
        },
        {
            "id": "l_town_20",
            "prompt": "What is the average water age in the network based on the last 24 hours of the simulation "
                      "Remember to consider the report time step such that 24 hours are represented by the last "
                      "24 * (3600 // d.getTimeReportingStep()) time steps",
            "command": "d.getComputedQualityTimeSeries().NodeQuality[-(24* (3600 // d.getTimeReportingStep())):, :].mean()",
            "args": {},
            "expected": 7.27984514201669,
            "category": "quality",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
        },
        {
            "id": "l_town_21",
            "prompt": "What is the max water age in the network based on the last 24 hours of the simulation "
                      "Remember to consider the report time step such that 24 hours are represented by the last "
                      "24 * (3600 // d.getTimeReportingStep()) time steps",
            "command": "d.getComputedQualityTimeSeries().NodeQuality[-(24* (3600 // d.getTimeReportingStep())):, :].max()",
            "args": {},
            "expected": 168.0,
            "category": "quality",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
        },
        {
            "id": "l_town_22",
            "prompt": "What is the standard deviation of water quality in the network based on the last 24 hours of "
                      "the simulation. Remember to consider the report time step such that 24 hours are represented by "
                      "the last 24 * (3600 // d.getTimeReportingStep()) time steps",
            "command": "d.getComputedQualityTimeSeries().NodeQuality"
                       "[-(24* (3600 // d.getTimeReportingStep())):, :].std()",
            "args": {},
            "expected": 13.220083917900434,
            "category": "quality",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
        },
        {
            "id": "l_town_23",
            "prompt": "What is the water age in junction {element_name} at time {t}? "
                      "Remember to consider the report time step. "
                      "hour t is represented by index: t * (3600 // d.getTimeReportingStep())",
            "command": "d.getComputedQualityTimeSeries().NodeQuality"
                       "[48 * (3600 // d.getTimeReportingStep()), d.getNodeIndex('n525')-1]",
            "args": {"element_name": 'n525', "t": 48},
            "expected": 0.3217929005622864,
            "category": "quality",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
        },
        {
            "id": "l_town_24",
            "prompt": "What is the max water age in junction {element_name}? ",
            "command": "d.getComputedQualityTimeSeries().NodeQuality[:, d.getNodeIndex('n525')-1].max()",
            "args": {"element_name": 'n525'},
            "expected": 1.3206589221954346,
            "category": "quality",
            "network": Path(os.path.join(networks_dir, "L-TOWN_water_age.inp")).as_posix()
        },
        ]


pa_queries = [
        {
            "id": "pa_1",
            "prompt": "Run a series of multiple simulations. "
                      "in each simulation multiply the base demands of all junctions by the following values: "
                      "[0.7, 0.8, 0.9, 1, 1.1, 1.2, 1.3, 1.4, 1.5]. "
                      "for each simulation record the min pressure at demand junctions "
                      "Demand junctions are junctions with base demand larger than 0. "
                      "return a dictionary with the min pressure for each demand factor. "
                      "To get the base demands of all nodes use: d.getNodeBaseDemands()[1]. "
                      "To set new base demands use d.setNodeBaseDemands(node, base_demand[node] * factor). "
                      "Note that the initial base demands should be hold outside the loop to keep them in their original value. "
                      "When calculating the pressures, don't forget to ignore tanks and reservoirs",
            "command": "",
            "args": {},
            "expected": "{0.7: 36.204986572265625, 0.8: 36.00179672241211, 0.9: 35.76666259765625, 1: 35.49851989746094, 1.1: 35.19639587402344, 1.2: 34.859230041503906, 1.3: 34.4860954284668, 1.4: 34.07614517211914, 1.5: 33.628353118896484}",
            "category": "iterative",
            "network": Path(os.path.join(networks_dir, "PA2.inp")).as_posix()
        },
        {
            "id": "pa_2",
            "prompt": "Conduct an evaluation of alternative pump curves."
                      "Consider the following candidate flows: [250, 300, 350] "
                      "and candidate heads: [45, 40, 35]. "
                      "Form all possible combinations of (flow, head), "
                      "of the two lists, resulting in 9 distinct (flow, head) pairs. "
                      "For each (flow, head) pair, do the following steps independently: "

                      "1. Create a new pump curve that contains exactly ONE point: [flow, head]. "
                      "Use: d.addCurve(curve_name, [flow, head]) "
                      "2. Assign this curve to the pump (pump index = 1) using: "
                      "d.setLinkPumpHCurve(d.getCurveIndex(curve_name), 1, [flow, head]) "
                      "3. Run a hydraulic simulation and compute the TOTAL energy consumption of the pump over the entire simulation horizon. "
                      "Only pump energy should be included, use pump indexes. "
                      "Store the result for each (flow, head) pair. Return a dictionary where: keys are the tuple of (flow, head) "
                      "and values are the total pump energy consumption for that curve. ",

            "command": "",
            "args": {},
            "expected": "{(250, 45): 65.51891660690308, (250, 40): 58.23881256580353, (250, 35): 50.959050357341766, (300, 45): 67.162318110466, (300, 40): 59.699774980545044, (300, 35): 52.23727202415466, (350, 45): 68.15333580970764, (350, 40): 60.58065617084503, (350, 35): 53.008138716220856}",
            "category": "iterative",
            "network": Path(os.path.join(networks_dir, "PA2.inp")).as_posix()
        },
        {
            "id": "pa_3",
            "prompt": "The pipe with ID 212 need to be replaced. "
                      "Available diameters are: [6, 8, 10, 12, 14]. "
                      "Try to replace the candidate diameters for pipe 212 to answer: "
                      "What is the minimal diameter that can be used for pipe 212 such that the pressure in all demand junctions will be above 30. "
                      "Demand junctions are junctions with base demand larger than 0. "
                      "To get the base demands of all nodes use: d.getNodeBaseDemands()[1]. "
                      "To replace a pipe diameter you can use the EPyT method d.setLinkDiameter()",
            "command": "",
            "args": {},
            "expected": "6",
            "category": "iterative",
            "network": Path(os.path.join(networks_dir, "PA2.inp")).as_posix()
        },
]

def get_queries(keywords):
    queries_map = {
        'net1': net1_queries,
        'net3': net3_queries,
        'l_town': l_town_queries,
        'pa': pa_queries,
        'dummy': dummy_queries,
        'single_dummy': single_dummy_query,
        'single_dummy_hard': single_dummy_hard
    }
    
    all_experiment_queries = ['net1', 'net3', 'l_town', 'pa']
    selected_queries = []
    if 'all' in keywords:
        for q_list in all_experiment_queries:
            selected_queries.extend(queries_map[q_list])
    else:
        for key in keywords:
            if key in queries_map:
                selected_queries.extend(queries_map[key])
    for q in selected_queries:
        q['prompt'] = q['prompt'].format(**q['args'])
    return selected_queries
