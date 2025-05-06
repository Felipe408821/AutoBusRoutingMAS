/*
* Name: ModeloBDI
* Author: A. Felipe Camacho Martínez
* Tags: UC3M
*/

model BDIModel

global {
	// Carga de archivos GeoJSON
    file roads_file <- file("/Users/felipe/PycharmProjects/GeoJsonMapGenerator/geojson/aristas.geojson");
    file nodes_file <- file("/Users/felipe/PycharmProjects/GeoJsonMapGenerator/geojson/nodos.geojson");
    file building_file <- file("/Users/felipe/PycharmProjects/GeoJsonMapGenerator/geojson/edificios.geojson");
    file bus_stop_file <- file("/Users/felipe/PycharmProjects/GeoJsonMapGenerator/geojson/paradas.geojson");
    geometry shape <- envelope(roads_file) #m;
    graph road_network;
    
    // ---------------------------------------------------------- CONTROL TEMPORAL ---------------------------------------------------------
    float step <- 1#s;
	float max_time <- 3600#s; // Duración de la simulación 1 hora - 3600s.
	float hora_init <- 12.00; // Hora de inicio de la simulación de [00:00 a 23:59].
	float init <- hora_init * 3600;
	
	// ---------------------------------------------------------------- RUTAS --------------------------------------------------------------
    intersection start_point_madrid;
    intersection start_point_gp;
    intersection start_point_macas;
    intersection start_point_l;
    intersection start_point_l2;
    
	list<bus_stop> route_651A;
	list<bus_stop> route_651B;
	list<bus_stop> route_652A;
	list<bus_stop> route_652B;
	list<bus_stop> route_l1;
	list<bus_stop> route_l2;
	
	list stops_651A <- ['06230', '09094', '07304', '06232', '06233', '06234', '06235', '06236', '06215', '06237', '06216', '06176', '06240', '11859', '11860', '11862', '11865', '11867', '09409', '06242', '11855', '10491', '18613', '06177', '12995'];
	list stops_651B <- ['06244', '18072', '18612', '11835', '11854', '11856', '11868', '11866', '11861', '06518', '06424', '06205', '06249', '06212', '06250', '06251', '06252', '06253', '06254', '06230'];
	list stops_652A <- ['06230', '09094', '07304', '06232', '06233', '06234', '06235', '06236', '06178', '11857', '11858', '17330', '17332', '17334', '18882', '20611'];
	list stops_652B <- ['20611', '17336', '17335', '17333', '17331', '06242', '06203', '06250', '06251', '06252', '06253', '06254', '06230','07305', '09093', '06256'];
	list stops_l1 <- ['17923', '17685', '11385', '11417', '12747', '12994', '12992', '18070', '12990', '12991', '12993', '12748', '18073', '18612', '11835', '11854', '11858', '17330', '18498', '11861', '06518', '06424', '06205', '17742', '12500', '12504', '06251', '06252', '06253', '06254', '13003', '17700', '12905', '12906', '12907', '09407', '12995', '11421', '08792', '12066', '09368', '08790', '08788', '12679', '15188', '17270', '11385', '17724', '17925', '17923'];
	list stops_l2 <- ['17923', '17924', '17683', '17725', '17721', '17269', '15189', '08787', '08789', '09368', '12067', '08791', '11420', '06244', '12271', '06429', '12908', '12909', '12910', '17699', '16386', '06232', '06233', '06234', '06235', '12503', '12499', '17743', '06176', '06240', '11859', '11860', '18497', '17331', '06242', '09409', '11855', '10491', '18613', '18071', '06245', '08796', '12994', '12992', '18070', '12990', '12991', '12993', '12989', '11418', '11386', '17684', '17924','17923'];
	list all_routes <- (stops_651A + stops_651B + stops_652A + stops_652B + stops_l1 + stops_l2);
	list<bus_stop> sub_bus_stops <- [];
    		
    map<string, list<bus_stop>> lineas_group;

	float frequency_651 <- 601#s; // 10 minutos
	float frequency_652 <- 901#s; // 15 minutos
	float frequency_l <- 1801#s; // 30 minutos
	
	float time_651 <- 0#s;
	float time_652 <- 0#s;
	float time_l <- 0#s;
	
	// --------------------------------------------- MODELO GENERACIÓN DE DEMANDA DE PASAJEROS ---------------------------------------------
	// Variables para la generación de la demanda de pasajeros
	float pi <- 3.141592653589793;
	float lambda_base <- 3; // Tasa base de generación de pasajeros (λ_0)
	float dem; // Dem(t)
	int event; // Event
	float prob_og; // ProbOg(v)
    float lambda; // λ(t, v)
    
    // Matriz Origen-Destino (OD) con probabilidades
    map<string, map<string, float>> OD_matrix <- [
        "07304" :: ["06236"::0.40, "20611"::0.20, "11385"::0.10, "17923"::0.05, "S"::0.25],
        "07305" :: ["07304"::0.00, "07305"::0.00, "06236"::0.00, "06250"::0.00, "20611"::0.00, "11385"::0.00, "17923"::0.00, "S"::0.00],
        "06236" :: ["20611"::0.30, "11385"::0.10, "17923"::0.05, "S"::0.40],
        "06250" :: ["07305"::0.40, "11385"::0.10, "17923"::0.05, "S"::0.20],
        "20611" :: ["07305"::0.30, "06250"::0.40, "11385"::0.05, "17923"::0.05, "S"::0.05],
        "11385" :: ["07305"::0.20, "06236"::0.20, "06250"::0.20, "20611"::0.05, "17923"::0.05, "S"::0.20],
        "17923" :: ["07305"::0.05, "06236"::0.05, "06250"::0.05, "20611"::0.05, "11385"::0.20, "S"::0.40],
        "S"     :: ["07304"::0.05, "07305"::0.20, "06236"::0.10, "06250"::0.20, "20611"::0.10, "11385"::0.10, "17923"::0.10, "S"::0.15]
    ];
    
    int frequency_passengers <- 1201#s; // 20 minutos
    float time_passengers <- 0#s;
	
	// TEMPORAL PRUEBAS
	bool comentarios <- false;
	bool pruebas <- false;

    // ------------------------------------------------------------- PREDICADOS ------------------------------------------------------------
   	predicate ruta_finalizada <- new_predicate("ruta_finalizada");

	// --------------------------------------------------------------- LOGS  ---------------------------------------------------------------
	list<list> logs_bus_generation;
	list<list> logs_bus_results;
	
	list<list> logs_passengers_generation;
	list<list> logs_passengers_results;
	
	list<list> logs_service_frequency;
	
	list<list> logs;
	
	list<list> saltos;
	
	list<list> logs_ruta_dinamicas;
    
    // ----------------------------------------------------------- INICIALIZACIÓN ----------------------------------------------------------	
    init {
        create intersection from: nodes_file;
        create building from: building_file;
        create bus_stop from: bus_stop_file;
        
        // Crear carreteras bidireccionales
        create road from: roads_file {
            create road {
                num_lanes <- myself.num_lanes;
                shape <- polyline(reverse(myself.shape.points));
                maxspeed <- myself.maxspeed;
                linked_road <- myself;
                myself.linked_road <- self;
            }
        }
        
        road_network <- as_driving_graph(road, intersection);
        
        start_point_madrid <- intersection(1618);
        start_point_gp <- intersection(430);
        start_point_macas <- intersection(108);
		start_point_l <- intersection(1381);
		start_point_l2 <- intersection(1146);
		
    	route_651A <- create_route(stops_651A);
    	route_651B <- create_route(stops_651B);
		route_652A <- create_route(stops_652A);
		route_652B <- create_route(stops_652B);
		route_l1 <- create_route(stops_l1);
		route_l2 <- create_route(stops_l2);
		
		lineas_group <- [
	    	"651A":: route_651A, 
	    	"651B":: route_651B,
	    	"652A":: route_652A,
	        "652B":: route_652B,
	        "L1":: route_l1,
	        "L2":: route_l2
	    ];
	    
	    // --------------------------------------------------------------- LOGS  ---------------------------------------------------------------
      	logs_bus_generation << ["bus", "linea", "hora"] + "\n";
      	logs_bus_results << ["bus", "linea", "hora", "ruta_finalizada", "num_pasajeros"] + "\n";
      	logs_service_frequency << ["parada", "frecuencias"];
       
        logs_passengers_generation << ["pasajero", "hora", "inicio", "ref_inicio", "destino", "ref_destino"] + "\n";
        logs_passengers_results << ["pasajero", "tiempo_espera", "tiempo_viaje", "tiempo_transbordo", "tiempo_total"] + "\n";
		
		if !pruebas{
			create bus with: [ruta: route_651A, hora_inicio: to_military_time(time), linea: "651A", location: start_point_madrid.location] number: 1;
	        create bus with: [ruta: route_651B, hora_inicio: to_military_time(time), linea: "651B", location: start_point_macas.location] number: 1;
	        create bus with: [ruta: route_652A, hora_inicio: to_military_time(time), linea: "652A", location: start_point_madrid.location] number: 1;
	        create bus with: [ruta: route_652B, hora_inicio: to_military_time(time), linea: "652B", location: start_point_gp.location] number: 1;
			create bus with: [ruta: route_l1, hora_inicio: to_military_time(time), linea: "L1", location: start_point_l.location] number: 1;
	        create bus with: [ruta: route_l2, hora_inicio: to_military_time(time), linea: "L2", location: start_point_l2.location] number: 1;
		} else {
			create bus with: [ruta: route_651A, hora_inicio: to_military_time(time), linea: "651A", location: start_point_madrid.location] number: 1;
			create bus with: [ruta: route_652A, hora_inicio: to_military_time(time), linea: "652A", location: start_point_madrid.location] number: 1;
		}
	
		list <bus_stop> c <- cut_bus_stops();
	}
    
    // -------------------------------------------------------- FUNCIONES AUXILIARES -------------------------------------------------------
	list<bus_stop> create_route (list<string> ref_codes){
		list<bus_stop> route <- [];
		 bus_stop stop;
		
   		loop ref_code over: ref_codes {
		    stop <- first(bus_stop where (each get "ref" = ref_code));
		    if stop != nil {
		        route <- route + [stop];
	   		}
		}
		return route;
	}
	
    reflex create_buses when: !pruebas {    	
        if (time - time_651 >= frequency_651) {
            create bus with: [ruta: route_651A, hora_inicio: to_military_time(time), linea: "651A", location: start_point_madrid.location] number: 1;
            create bus with: [ruta: route_651B, hora_inicio: to_military_time(time), linea: "651B", location: start_point_macas.location] number: 1;
            time_651 <- time;
        }
        if (time - time_652 >= frequency_652) {
            create bus with: [ruta: route_652A, hora_inicio: to_military_time(time), linea: "652A", location: start_point_madrid.location] number: 1;
            create bus with: [ruta: route_652B,hora_inicio: to_military_time(time), linea: "652B", location: start_point_gp.location] number: 1;
            time_652 <- time;
        }
        if (time - time_l >= frequency_l) {
            create bus with: [ruta: route_l1, hora_inicio: to_military_time(time), linea: "L1", location: start_point_l.location] number: 1;
            create bus with: [ruta: route_l2, hora_inicio: to_military_time(time), linea: "L2", location: start_point_l2.location] number: 1;
            time_l <- time;
        }
    }
    
    list<bus_stop> cut_bus_stops {
    	sub_bus_stops <- [];
    	bus_stop stop;
    	
    	loop ref_code over: all_routes {
    		stop <- first(bus_stop where (each get "ref" = ref_code));
    		if (stop != nil) and (not (stop in sub_bus_stops)){
    			sub_bus_stops <- sub_bus_stops + stop;
    		}
    	}
    	return sub_bus_stops;
    }
    
    // -------------------------------------------------------------- EVENTOS --------------------------------------------------------------
    // Función para bloquear aleatoriamente carreteras
    reflex block_road{
    	bool block <- flip(0.005); 

    	if (block) {
			road calle_cortada <- one_of(road);
			ask calle_cortada {
                color <- #red;
                blocked <- true;
            }   
            
            road_network <- as_driving_graph((road_network.edges-calle_cortada), intersection);
            if (comentarios){
            	write "[INFO] Incidente se ha cortado la siguiente calle " + calle_cortada;
            }
    	}
    }
    
    // Función para generar tráfico aleatoriamente en las carreteras
    reflex traffic_road{
    	bool traffic <- flip(0.01); 
        if (traffic) {
			road calle_trafico <- one_of(road_network.edges);
    		ask calle_trafico {
                color <- #orange;
                traffic <- true;
                maxspeed <- maxspeed * 0.75;
            }
            if (comentarios){
            	write "[INFO] Tráfico lento en la siguiente calle " + calle_trafico;
            }
        }
    }
    
    // ---------------------------------------------- MODELO GENERACIÓN DE DEMANDA DE PASAJEROS ----------------------------------------------
    // Función sinusoidal para la variación de la demanda a lo largo del día
    float calculate_dem(float t){
    	return 1 + 0.5 * sin((2 * pi / 10 * (t-5)) * (180/pi)) + 0.5 * sin((2 * pi / 10 * (t-16)) * (180/pi));
    }
    
    // Función para calcular la probabilidad de que una parada sea un origen
	float calculate_prob(string origen) {
		map<string, float> destinos;
		if (OD_matrix.keys contains origen) {
		    destinos <- OD_matrix[origen];
		    return sum(destinos);
		} else {
		    destinos <- OD_matrix["S"];
		    return sum(destinos);
		}
	}
    
    // Función para generar pasajeros usando una distribución de Poisson
    int calculate_poisson(float t, bus_stop v, int event) {
        dem <- calculate_dem(t); // Dem(t)
        prob_og <- calculate_prob(v get "ref"); // ProbOg(v)
        lambda <- lambda_base * dem * event * prob_og; // λ(t, v)
        return poisson(lambda); // Generar pasajeros usando una distribución de Poisson
    }
    
    // Función para generar el número de pasajeros en cada parada
	map<bus_stop, int> generate_passengers(float t) {
	    int aux;
	    int aux_suma;
    	map<bus_stop, int> passengers_per_stop;
       
	    event <- one_of ([1,1,1,1,1,1,1,1,1,2]); // Event
	    
	    // IMPORTANTE Aquí generaremos solo pasajeros en paradas que tengan rutas asignadas
	    loop v over: sub_bus_stops {
	    	aux <- calculate_poisson(t, v, event);
	    	aux_suma <- aux_suma + aux;
	    	passengers_per_stop[v] <- aux;
	    }
	    return passengers_per_stop;
	}

	// Función para asignar destinos a los pasajeros
	bus_stop assign_destination(string origen) {
		map<string, float> destinos;
		if (OD_matrix.keys contains origen) {
		    destinos <- OD_matrix[origen];
		} else {
		    destinos <- OD_matrix["S"];  
		}
	    list<string> destinos_lista <- keys(destinos);
	    list<float> probabilidades <- values(destinos);
	    
	    float random_value <- rnd(0.0, 1.0);
	    float cumlative_prob <- 0.0;
	    int index <- 0;
	    
	    loop i from: 0 to: length(probabilidades)-1 {
		    cumlative_prob <- cumlative_prob + probabilidades[index];
	        if (random_value <= cumlative_prob) {
	        	index <- i;
	            break;
	        }
	        index <- i;
	    }
	    
	    if destinos_lista[index] != "S"{
	    	return first(sub_bus_stops where (each get "ref" = destinos_lista[index]));
	    } else {
	    	return one_of(sub_bus_stops);
	    }
	}
	
	// Función que ensambla los datos para generar los pasajeros
	int assemble_passenger(float t){
		map<bus_stop, int> aux_generados <- generate_passengers(t);
		int total_generados <- 0;

	    loop v over: aux_generados.keys {
	    	loop i from: 1 to: aux_generados[v] {
		    	bus_stop parada_destino <- assign_destination(v.name);
		    	create passenger with: [location: v.location, hora_inicio: to_military_time(time), parada_inicial: v, destino: [parada_destino]];
		    	total_generados <- total_generados + 1;
	    	}
	    }
	    
	    return total_generados;
	}

	// Función que genera pasajeros cada X tiempo
	reflex passengers {
		if mod(int(time), frequency_passengers) = 0 {
			int hora <- ((init + time) / 3600) mod 24;
			float minutos <- (((init + time) mod 3600) / 60) / 60;
			float aux <- hora + minutos;
			int generados <- assemble_passenger(aux);
			
			// PRUEBAS
			/*
			bus_stop iniciooo <- first(bus_stop where (each get "ref" = "06176"));
			bus_stop destinooo <- first(bus_stop where (each get "ref" = "20611"));
			create passenger with: [location: iniciooo.location, hora_inicio: to_military_time(time), parada_inicial: iniciooo, destino: [destinooo]] number: 21;
			
			write "1. Pasajeros prueba inicio: " + iniciooo + iniciooo.name + " con destino " + destinooo + destinooo.name;
			
			iniciooo <- first(bus_stop where (each get "ref" = "16386"));
			destinooo <- first(bus_stop where (each get "ref" = "17743"));
			create passenger with: [location: iniciooo.location, hora_inicio: to_military_time(time), parada_inicial: iniciooo, destino: [destinooo]] number: 21;
			
			write "2. Pasajeros prueba inicio: " + iniciooo + iniciooo.name + " con destino " + destinooo + destinooo.name;
		    
		    bus_stop iniciooo <- bus_stop(136);
			bus_stop destinooo <- bus_stop(1);
			create passenger with: [location: iniciooo.location, hora_inicio: to_military_time(time), parada_inicial: iniciooo, destino: [destinooo]] number: 19;
			
			write "1. Pasajeros prueba inicio: " + iniciooo + iniciooo.name + " con destino " + destinooo + destinooo.name;
			
		    bus_stop iniciooo <- bus_stop(136);
			bus_stop destinooo <- bus_stop(128);
			create passenger with: [location: iniciooo.location, hora_inicio: to_military_time(time), parada_inicial: iniciooo, destino: [destinooo]] number: 15;
			
			write "2. Pasajeros prueba inicio: " + iniciooo + iniciooo.name + " con destino " + destinooo + destinooo.name;
		    */
			//write "[HORA]: horas: " + aux + ", en hora militar: " + to_military_time(init + time) + " se han generado un total de " +  generados + " pasajeros.";
			write "\n";
		}
	}
    
	string to_military_time(float h) {
	    int hours <- (h / 3600) mod 24; int minutes <- int((h mod 3600) / 60); int seconds <- int(h mod 60);

	    string str_hours <- (hours < 10) ? "0" + hours : "" + hours;
	    string str_minutes <- (minutes < 10) ? "0" + minutes : "" + minutes;
	    string str_seconds <- (seconds < 10) ? "0" + seconds : "" + seconds;
	    
	    return str_hours + ":" + str_minutes + ":" + str_seconds;
	}
    
    // ------------------------------------------------------------ FINALIZACIÓN -----------------------------------------------------------	
    reflex end_simulation when: empty(bus where !each.has_belief(ruta_finalizada)) or time = max_time{
    	string h <- to_military_time(time);
    	
    	ask bus{
    		logs_bus_results << [string(self), self.linea, self.hora_fin, has_belief(ruta_finalizada), (self.capacidad_maxima - self.plazas_disponibles)] + "\n";
    		write "[INFO] "  + string(self) + " Ha finalizado su ruta con " + (self.capacidad_maxima - self.plazas_disponibles) + " pasajeros." + self.passengers;
    	}

    	ask passenger {
    		logs_passengers_results << [string(self), self.tiempo_espera, self.tiempo_viaje, self.tiempo_transbordo, self.tiempo_total] + "\n";
    		//write "[TIEMPOS] " + string(self) + " tiempos de espera: " + self.tiempo_espera + " viaje: " + self.tiempo_viaje + " transbordo: " + self.tiempo_transbordo +  " total: " + self.tiempo_total;
		}
		
		ask bus_stop {
	      	logs_service_frequency << [self get "ref", self.frecuencia_por_linea];
		}
	
		if !pruebas{
			save logs_bus_generation to: "exports/bus_generation_basic.csv"; 
			save logs_bus_results to: "exports/bus_results_basic.csv";
			save logs_service_frequency to: "exports/service_frequency.csv";
					
			save logs_passengers_generation to: "exports/passengers_generation_basic.csv"; 
			save logs_passengers_results to: "exports/passengers_results_basic.csv"; 

			save logs to: "exports/passengers.csv"; 	
			save saltos to: "exports/saltos.csv"; 
			
			save logs_ruta_dinamicas to: "exports/dinamica.csv"; 
		}
		do pause;
	}
}



// -------------------------------------------------------------------------------------------------------------------------------------
// -------------------------------------------------------------- MAPA -----------------------------------------------------------------
// -------------------------------------------------------------------------------------------------------------------------------------
species road skills: [road_skill] {
	bool blocked <- false;
	bool traffic <- false;
    rgb color <- rgb(64, 64, 64); // Color de las carreteras
    
    aspect base {
        draw shape color: color end_arrow: 1;
    }
}

species intersection skills: [intersection_skill] ;

species building {
    rgb color <- rgb(170, 170, 170); // Color de los edificios
    aspect base {
        draw shape color: color;
    }
}


// -------------------------------------------------------------------------------------------------------------------------------------
// ------------------------------------------------------------- PARADAS ---------------------------------------------------------------
// -------------------------------------------------------------------------------------------------------------------------------------
species bus_stop skills: [fipa] {
	// --------------------------------------------------------- ESTADO INTERNO ------------------------------------------------------------
	bool ocupada <- false; // Booleano que indica si la parada está siendo utilizada por un bus para operaciones de embarque o desembarque.
	bool bloqueada <- false; // Booleano que indica si una parada es inaccesible.
	bool soporte_recibido <- false; // Booleano que indica si una parada ha recibido apoyo debido a la saturación por el número de pasajeros que se encuentra en ella.
	int total_pasajeros <- 0; // Número total de pasajeros que se encuentran esperando en la parada.
	int alerta_saturacion <- 20; // Umbral de saturación de una parada.
	map<bus_stop, int> destino_pasajeros; // Agrupación del número de pasajeros por destino en la parada.
	map<string, list<string>> frecuencia_por_linea; // Frecuencia de cada servicio o linea por parada, cuantos autobuses paran en la parada durante la simulación.
	map<string, map<bus, float>> tiempos_estimados_llegada; // Listado de las estimaciones temporales de los próximos buses que pasarán por la parada.
	
	// ------------------------------------------------ PROTOCOLOS DE COMUNICACIÓN FIPA ----------------------------------------------------
	
	// ------------------------------------------------ WORKING IN PROGRESS ----------------------------------------------------
	map<bus_stop, int> respuestas_esperadas_cfp;
	map<message, float> listado_propuestas;
	
	reflex parada_saturada when: (total_pasajeros > alerta_saturacion) and (!soporte_recibido) {
		// Protocolo 1: Notificación parada saturada
		// TENER EN CUENTA QUE SE PUEDE SATURAR MÁS DE UNA VEZ, COMO CONSIDERAMOS ESTO?
		// AQUI TENEMOS QUE COMPROBAR SOPORTE RECIBIDO POR DESTINO DINAMICO, PORQUE EL BUS CUANDO ACEPTE Y LLEGUE ENVIARÁ UN INFORM-DONE Y AHÍ SE PODRÁ RESETEAR ESE SOPORTE, YA QUE SE PUEDE VOLVER A SATURAR MÁS ADELANTE

		list<bus> buses_disponibles <- bus where (each.has_belief(ruta_finalizada) = false);
		
		if buses_disponibles != nil {
			loop d over: destino_pasajeros.pairs where (each.value > 5){
				
				loop b over: buses_disponibles {
					do start_conversation to: [b] protocol: 'fipa-contract-net' performative: "cfp" contents: ["[PARADA] Solicitud de apoyo", d.key, d.value, self];
					logs_ruta_dinamicas << [string(self), time, d.key, d.value, buses_disponibles] + "\n";
				}
				
				write "\n";
				
				write "Parada " + self + " pide soporte a " + buses_disponibles + " con destino " + destino_pasajeros;
    		
				write "\n";
				
				respuestas_esperadas_cfp[d.key] <- length(buses_disponibles);	
				soporte_recibido <- true;
			}
		} else {
			write "[FALLO_COBERTURA_SERVICIO] Parada saturada sin buses de apoyo disponibles.";
		}
	}
	
	reflex receive_propose when: !empty(proposes) {
		message propose <- proposes[0];
		list content <- list(propose.contents);
		
		if content[0] = "[BUS] Disponible" {
			// Protocolo 1: Notificación parada saturada
			write "Se recibe propuesta " + propose;
			listado_propuestas[propose] <- content[1];
			do procesar_propuestas(self, bus_stop(content[2]));
		}
	}
	
	reflex receive_refuse when: !empty(refuses) {
		message rechazo <- refuses[0];
		list content <- list(rechazo.contents);
		
		if content[0] = "[BUS] No me encuentro disponible" {
			// Protocolo 1: Notificación parada saturada
			write "Se recibe un rechazo " + rechazo;
			do procesar_propuestas(self, bus_stop(content[2]));
		}
	}
	
	action procesar_propuestas (bus_stop inicio_dinamico, bus_stop destino_dinamico){
		// Protocolo 1: Notificación parada saturada
		respuestas_esperadas_cfp[destino_dinamico] <- respuestas_esperadas_cfp[destino_dinamico] - 1;
			
		if respuestas_esperadas_cfp[destino_dinamico]  = 0 {
			
			map<message, float> aux_propus <- reverse(listado_propuestas.pairs sort_by (each.value));

			loop i over: aux_propus.keys {
				if i.contents[2] != destino_dinamico{
					remove key: i from: aux_propus;
				}
			}

			do accept_proposal message: message(first(aux_propus.pairs).key) contents: [inicio_dinamico, destino_dinamico];
			
			remove key: first(aux_propus.pairs).key from: listado_propuestas;
			remove key: first(aux_propus.pairs).key from: aux_propus;

			loop i over: aux_propus.keys {
				do reject_proposal message: message(i) contents: [];
				remove key: i from: listado_propuestas;
				remove key: i from: aux_propus;
			}
		}
	}
	// ------------------------------------------------ WORKING IN PROGRESS ----------------------------------------------------
	
	
	reflex receive_request when: !empty(requests) {
		message peticion <- requests[0];
		list content <- list(peticion.contents);
		
		if content[0] = "Solicitud E.T.A.s" {
			// Protocolo 7: Solicitud de tiempos estimados de llegada
			if tiempos_estimados_llegada != nil {
				do agree message: peticion contents: ["Solicitud E.T.A.s", tiempos_estimados_llegada];
			} else {
				do refuse message: peticion contents: ["No disponible solicitud E.T.A.s"];
			}
		}
	}
	
	reflex receive_inform when: !empty(informs) {
		message info <- informs[0];
		list content <- list(info.contents);
		
		if content[0] = "Parada inaccesible" {
			// Protocolo 5: Notificación parada inaccesible
			list<passenger> waiting_passengers <- passenger overlapping (self.location);
			loop p over: waiting_passengers {
				do start_conversation to: [p] protocol: "no-protocol" performative: "inform" contents: ["Inicio inaccesible", content[1], content[2]]; 
			}
		} else if content[0] = "Estimación de llegada a la parada"{
			// Protocolo 6: Notificación de tiempo estimado de llegada
	        if tiempos_estimados_llegada[content[1]] != nil {
	        	tiempos_estimados_llegada[content[1]] <- tiempos_estimados_llegada[content[1]] + map([content[2] :: content[3]]);
	        } else {
	        	tiempos_estimados_llegada[content[1]] <- map([content[2] :: content[3]]);
	        }
		} else if content[0] = "Registro servicio" {
			// Protocolo 8: Registro frecuencia del servicio
	        if frecuencia_por_linea[content[1]] != nil {
	        	frecuencia_por_linea[content[1]] << content[2];
	        } else {
	        	frecuencia_por_linea[content[1]] <- [content[2]];
        	}	
		} else if content[0] = "[BUS] Ruta dinámica incorporada" {
			// Protocolo 1: Notificación parada saturada
		}
		
		do end_conversation message: info contents: [];
	}
	
	// ------------------------------------------------------------- ACCIONES --------------------------------------------------------------
	action update_passengers {
		total_pasajeros <- 0;
		loop p over: destino_pasajeros.values{
			total_pasajeros <- total_pasajeros + p;
		}
	}

	// -------------------------------------------------------------- ASPECTO --------------------------------------------------------------
    aspect base {
    	string ruta;
    	if !bloqueada and not(total_pasajeros > alerta_saturacion) {
    		ruta <- "/Users/felipe/PycharmProjects/GeoJsonMapGenerator/images/parada.png";
    	} else if total_pasajeros > alerta_saturacion {
    		ruta <- "/Users/felipe/PycharmProjects/GeoJsonMapGenerator/images/parada-s.png";
    	} else {
    		ruta <- "/Users/felipe/PycharmProjects/GeoJsonMapGenerator/images/parada-b.png";
    	}
        draw image(ruta) size: {10, 15};
    }
}


// -------------------------------------------------------------------------------------------------------------------------------------
// --------------------------------------------------------------- BUS -----------------------------------------------------------------
// -------------------------------------------------------------------------------------------------------------------------------------
species bus skills: [driving, fipa] control: simple_bdi {
    // ------------------------------------------------------------ CREENCIAS --------------------------------------------------------------
    predicate ruta_asignada;
    predicate en_parada <- new_predicate("en_parada");
    predicate desembarcar <- new_predicate("desembarcar");
    predicate propus_enviadas <- new_predicate("propus_enviadas");
    predicate registro_llegada <- new_predicate("registro_llegada");
    predicate embarque_completo <- new_predicate("embarque_completo");
 
    string hora_inicio;
    string hora_fin;
    string linea;
    
    int capacidad_maxima;
    int plazas_disponibles;
	int espera <- 0;
	int respuestas_esperadas;
	int respuestas_recibidas;
    
    bool ruta_calculada <- false;	
    bool ultima_parada <- false;
    
    intersection interseccion_siguiente_parada;
    
    bus_stop siguiente_parada;	
	bus_stop parada_actual;
    
    list<bus_stop> ruta;
    
    list<passenger> passengers <- []; // Pasajeros en el autobús
    
    // -------------------------------------------------------------- DESEOS ---------------------------------------------------------------
    predicate completar_ruta <- new_predicate("completar_ruta");
    predicate embarcar_pasajeros <- new_predicate("embarcar_pasajeros");
    predicate gestionar_parada <- new_predicate("gestionar_parada");

    // --------------------------------------------------------- INICIALIZACIÓN ------------------------------------------------------------
    init {
        vehicle_length <- 12 #m; // Longitud de un autobús
        max_speed <- 100 #km / #h; // Velocidad máxima permitida
        max_acceleration <- 1.92; // Aceleración
        capacidad_maxima <- 86; 
        plazas_disponibles <- capacidad_maxima;
        siguiente_parada <- ruta[0];
        
        ruta_asignada <- new_predicate("ruta_asignada", ["ruta"::ruta, "linea"::linea]);
        do add_belief(ruta_asignada);

        do add_desire(completar_ruta);
        
	    logs_bus_generation << [string(self), linea, hora_inicio] + "\n";
    }
    
	// ------------------------------------------------------ INTENCIONES / PLANES ---------------------------------------------------------
	plan ruta intention: completar_ruta {
		if has_belief(ruta_finalizada){
			do remove_intention(get_predicate(get_current_intention()), true);
			do current_intention_on_hold();
		} else {
			if not ruta_calculada {
				do calcular_ruta;
	            do inform_estimated_time_arrival;
	        }
	
	        if current_path != nil {
	            do drive;
	        }
	    	
			if current_path = nil and interseccion_siguiente_parada.location = self.location {
				parada_actual <- siguiente_parada;
				
				if parada_actual.ocupada {
		        	espera <- espera + 1;
		        	if espera > 20 {
						espera <- 0;
						
		        		write "BUS SALTA " + self + self.linea + parada_actual + parada_actual.name;
    		    		saltos << [string(self),parada_actual, parada_actual.name] + "\n";
						
				        do desembarcar_pasajeros;
			 
		    			do reanudar_ruta("saltar");
			        }
				} else {					
		            parada_actual.ocupada <- true;
		            
		            write "\n";
					write "BUS BLOQUEA " + self + " " + linea + " " + parada_actual + " " + parada_actual.name + " " + parada_actual get "ref" + " " +  parada_actual.ocupada;
		            
		            do add_subintention(get_current_intention(), gestionar_parada, true);
		            do current_intention_on_hold();
	            }
			} 	
		}
	}
	
    plan gestionar_parada intention: gestionar_parada {
    	if not has_belief(registro_llegada) {
	        do registrar_llegada;
    		do add_belief(registro_llegada);
    	}
    	
    	if not has_belief(desembarcar) {
        	do desembarcar_pasajeros;
        	do add_belief(desembarcar);
        }
        
        if not ultima_parada and plazas_disponibles > 0 {
        	do add_subintention(get_current_intention(), embarcar_pasajeros, true);
            do current_intention_on_hold(); 
	    } else {
	    	do add_belief(embarque_completo);
	    }
        
        if has_belief(embarque_completo) {
        	do remove_belief(registro_llegada);
        	do remove_belief(desembarcar);
        	do remove_belief(propus_enviadas);
        	do remove_belief(embarque_completo);
        	
        	do remove_desire(embarcar_pasajeros);
        	do reanudar_ruta("desocupar");
        }
    }
	
    // ----------------------------------------------------------- SUBPLANES ---------------------------------------------------------------
	action desembarcar_pasajeros {
        // Protocolo 3: Desembarque de pasajeros
        list<passenger> passengers_to_remove <- [];

        loop p over: passengers {
            if p.destino[0].location = interseccion_siguiente_parada.location {
                passengers_to_remove << p;
                plazas_disponibles <- plazas_disponibles + 1;
                
                logs << ["BAJA/TRANSBORDO",string(self), p, parada_actual, parada_actual.name, p.destino] + "\n";
                
                //write "BAJA/TRANSBORDO" + string(self) + p + parada_actual + parada_actual.name + p.destino;
                
                if length(p.destino) > 1 {
                	do start_conversation to: [p] protocol: "no-protocol" performative: "inform" contents: ["Transbordo alcanzado", p.destino[0], p.destino[0].location];
                } else {
                	do start_conversation to: [p] protocol: "no-protocol" performative: "inform" contents: ["Destino alcanzado", p.destino[0]];
                }
            }
        }
        
        passengers <- passengers - passengers_to_remove;
    }
    
	plan embarcar_pasajeros intention: embarcar_pasajeros {
		//write "1.Embarque";
		if not has_belief(propus_enviadas){
			//write "2.Embarque: Enviar propus";
			do cfp_embarque;
			do add_belief(propus_enviadas);
		}
		
		if has_belief(embarque_completo){
			//write "3.Embarque: Completado";
			do remove_intention(get_predicate(get_current_intention()), true);
		}
	}
   
	// ------------------------------------------------------------- ACCIONES --------------------------------------------------------------
    action calcular_ruta {
        if not empty(ruta) {
		    siguiente_parada <- ruta[0];
		}
		
        interseccion_siguiente_parada <- find_intersection(siguiente_parada);
        
        if interseccion_siguiente_parada != nil and interseccion_siguiente_parada != self.location {
            do compute_path graph: road_network target: interseccion_siguiente_parada;
            
			if length(ruta) = 1 {
                ultima_parada <- true;
            } else {
                ruta <- ruta - ruta[0];
    		}
            
            ruta_calculada <- true;
        }
    }
    
    action cfp_embarque {		
        list<passenger> waiting_passengers <- passenger overlapping (interseccion_siguiente_parada.location);
        list<passenger> contact_passengers <- [];
        respuestas_esperadas <- 0;
        
        //write "BUS " + self + " plazas " + self.plazas_disponibles + self.passengers + " parada " + parada_actual + " pasajeros " + waiting_passengers;
               
        if not empty(waiting_passengers) {    
        	// Protocolo 4: Embarque de pasajeros         	
        	loop p over: waiting_passengers{
				do start_conversation to: [p] protocol: 'fipa-contract-net' performative: "cfp" contents: ["¿Quieres subir?", ruta, linea, self];
				contact_passengers << p;
        	}
        	
        	respuestas_esperadas <- length(contact_passengers);
        } else {
        	do add_belief(embarque_completo);
        }
    }
    
    action reanudar_ruta (string aux) {
    	if aux = "desocupar"{
	    	parada_actual.ocupada <- false;
    		write "BUS DESBLOQUEA " + self + parada_actual + parada_actual.ocupada;
    		do remove_intention(get_predicate(get_current_intention()), true);
    	} 
    	
    	if parada_actual.tiempos_estimados_llegada[linea] != nil and parada_actual.tiempos_estimados_llegada[linea][self] != nil {
            parada_actual.tiempos_estimados_llegada[linea] <- parada_actual.tiempos_estimados_llegada[linea] - (self::parada_actual.tiempos_estimados_llegada[linea][self]);
        }
        
        if ultima_parada {
        	write "Última_parada";
        	hora_fin <- time;
            do add_belief(ruta_finalizada);
        } else {
            ruta_calculada <- false;	
        }
    }
	
    intersection find_intersection (bus_stop parada) {
        return first(intersection where (distance_to(each.location, parada.shape.location) = 0));
    }
    
    float calculate_estimated_time_arrival(point destino) {
        float velocidad_promedio <- 30.0;
        float distancia_total <- distance_to(self.location, destino);
        return ((distancia_total / 1000.0) / velocidad_promedio) * 60;
    }
        
	string to_military_time(float h) {
	    int hours <- (h / 3600) mod 24; int minutes <- int((h mod 3600) / 60); int seconds <- int(h mod 60);

	    string str_hours <- (hours < 10) ? "0" + hours : "" + hours;
	    string str_minutes <- (minutes < 10) ? "0" + minutes : "" + minutes;
	    string str_seconds <- (seconds < 10) ? "0" + seconds : "" + seconds;
	    
	    return str_hours + ":" + str_minutes + ":" + str_seconds;
	}
    
	// ------------------------------------------------ PROTOCOLOS DE COMUNICACIÓN FIPA ----------------------------------------------------
	
	// ------------------------------------------------ WORKING IN PROGRESS ----------------------------------------------------
	
	reflex receive_cfps when: !empty(cfps) {
		message propose <- cfps[0];
		list content <- list(propose.contents);
		
		logs_ruta_dinamicas << [string(self), time, content] + "\n";
		write "RECIBI " + self + time + content;
		
		if content[0] = "[PARADA] Solicitud de apoyo" {
			// Protocolo 1: Notificación parada saturada
			if (plazas_disponibles > int(content[2])) {
				float utilidad <- calcular_utilidad( bus_stop(content[3]), bus_stop(content[1]), int(content[2]));
				logs_ruta_dinamicas << [string(self), time, utilidad, content] + "\n";
				write "Propose " + self + time + content;
				do propose message: propose contents: ["[BUS] Disponible", utilidad, content[1]];
			} else {
				write "Refuse " + self + time + content;
				do refuse message: propose contents: ["[BUS] No me encuentro disponible"];
			}
			
		}
	}
	
	// -------------------
	
	float factor_pertenencia (bool nuevo_inicio, bool nuevo_destino) {
		// EVALUA SI TANTO EL INICIO COMO EL DESTINO YA ESTÁN EN LA RUTA DEL BUS
		if nuevo_inicio and nuevo_destino {
			return 2;
		} else if !nuevo_inicio and !nuevo_destino {
			return 1;
		} else {
			return 1.5;
		}
	}
	
	float factor_cercania (int pos_nuevo_inicio) {
		// FACTOR PARA DETERMINAR LA CERCANIA NOS SERVIRÁ PARA EVALUAR LA CALIDAD DEL DATO DE FACTORES COMO EL DE LA CAPACIDAD, PARA MEDIR LA 
		// CUANTO MÁS CERCA ESTEMOS MEJOR POR LO QUE SE DEBERÁ EVALUAR COMO SUMA PARA LA UTILIDAD
		if pos_nuevo_inicio != 0 {
			return (1 / (1 + pos_nuevo_inicio));
		} else {
			return 0;
		}
	}
	
	float factor_capacidad (int plazas_requeridas) {
		// EVALUA SI EL BUS PUEDE CUBRIR LA CAPACIDAD EN SU TOTALIDAD O EN X PORCENTAJE
		if plazas_disponibles >= plazas_requeridas {
			return 1;
		} else {
			return plazas_disponibles / plazas_requeridas;	
		}
	}
	
	float factor_proximidad (float distancia_inicio, float distancia_destino) {
		// EVALUA SI LAS PARADAS NUEVAS A INCLUIR ESTÁN A MENOS DE 500 METROS DE ALGUNA PARADA QUE EXISTA YA EN LA RUTA, SIEMPRE Y CUANDO SEAN NUEVAS A INCLUIR SI YA EXISTE NO
		if (distancia_inicio < 500) and (distancia_destino < 500) {
			return 2;
		} else if (distancia_inicio < 500) or (distancia_destino < 500) {
			return 1.5;
		} else {
			return 1;
		}
	}
	
	
	float calcular_utilidad (bus_stop nuevo_inicio, bus_stop nuevo_destino, int plazas_requeridas) {
	    float utilidad <- 0.0; float distancia_inicio <- 0.0; float distancia_destino <- 0.0;
   	 	list<bus_stop> ruta_simulada <- ruta;
   	
    	// STEP 0 ------------------------------------------
	    // Comprobamos si ya están en la ruta actual
    	bool nuevo_inicio_en_ruta <- nuevo_inicio in ruta;
	    bool nueva_destino_en_ruta <- nuevo_destino in ruta;
	    
	    // STEP 1 ------------------------------------------
	    float f_pertenencia <- factor_pertenencia(nuevo_inicio_en_ruta, nueva_destino_en_ruta);
	    
	    /*write "\n";
	    write "[BUS] " + self + " linea " + linea;
	    write "Calcular utilidad " + nuevo_inicio + " " + nuevo_destino;
	    write "[STEP 1] f_pertenencia " + f_pertenencia + "\n";*/
	    
	    // STEP 2 ------------------------------------------
		if not nuevo_inicio_en_ruta {
			//write "[STEP 2] Se debería incluir " + nuevo_inicio + " como nueva parada.";
			
       		int mejor_posicion <- 0;
	        float menor_distancia <- 999999;
	
	        loop i from: 0 to: max((length(ruta_simulada) - 2), 0) {
	            float d1 <- distance_to(ruta_simulada[i].location, nuevo_inicio.location);
	            float d2 <- 1.0;
	            
	            if i + 1 < length(ruta_simulada) {
	            	d2 <- distance_to(ruta_simulada[i+1].location, nuevo_inicio.location);
	            }
	            
	            float total <- d1 + d2;
	
	            if total < menor_distancia {
	                menor_distancia <- total;
	                mejor_posicion <- i + 1;
	            }
	        }
	        distancia_inicio <- menor_distancia;
	        
	        list<bus_stop> parte_antes <- ruta_simulada[0::mejor_posicion];
			list<bus_stop> parte_despues <- ruta_simulada[mejor_posicion::length(ruta_simulada)];
			ruta_simulada <- parte_antes + [nuevo_inicio] + parte_despues;
	        
		} else {
			distancia_inicio <- 1;
			//write "[STEP 2] No haría falta incluir " + nuevo_inicio + " como nueva parada.";
		}
		
		// write "[STEP 2] distancia_inicio " + distancia_inicio;
	
	    if not nueva_destino_en_ruta {
	    	//write "[STEP 2] Se debería incluir " + nuevo_destino + " como nueva parada.";
	    	
	        int mejor_posicion <- 0;
	        float menor_distancia <- 999999;
	
	        loop i from: 0 to:(length(ruta_simulada) - 2) {
	            float d1 <- distance_to(ruta_simulada[i].location, nuevo_destino.location);
	            float d2 <- 1.0;
	            
	            if i + 1 < length(ruta_simulada) {
	            	d2 <- distance_to(ruta_simulada[i+1].location, nuevo_inicio.location);
	            }
	            
	            float total <- d1 + d2;
	
	            if total < menor_distancia {
	                menor_distancia <- total;
	                mejor_posicion <- i + 1;
	            }
	        }
	        distancia_destino <- menor_distancia;
	        
       		list<bus_stop> parte_antes <- ruta_simulada[0::mejor_posicion];
			list<bus_stop> parte_despues <- ruta_simulada[mejor_posicion::length(ruta_simulada)];
			ruta_simulada <- parte_antes + [nuevo_destino] + parte_despues;
	    } else {
	    	distancia_destino <- 1;
			//write "[STEP 2] No haría falta incluir " + nuevo_destino + " como nueva parada.";
		}
	    	        
	   	//write "[STEP 2] distancia_destino " + distancia_destino;
	    	        
		// STEP 2B  ------------------------------------------
		int pos_nuevo_inicio <- ruta index_of nuevo_inicio;
		
		if pos_nuevo_inicio < 0 {
			pos_nuevo_inicio <- ruta_simulada index_of nuevo_inicio;
		}
		
		float f_cercania <- factor_cercania(pos_nuevo_inicio);
		
		//write "[STEP 2B] Posición de la parada que solicita soporte " + pos_nuevo_inicio;
		//write "[STEP 2B] f_cercania " + f_cercania;
		
		// STEP 2C  ------------------------------------------
		float f_capacidad <- factor_capacidad(plazas_requeridas);
		//write "[STEP 2C] f_capacidad " + f_capacidad;
		
		// STEP 2 CONSOLIDACIÓN ------------------------------
		//write "[STEP 2] f_cercania * f_capacidad " + (f_cercania * f_capacidad) + "\n";
		
	    // STEP 3 ------------------------------------------
	    float distancia_inicio_act <- distance_to(self.location, nuevo_inicio.location);
	    // write "[STEP 3] distancia_inicio " + (1 / (1 + distancia_inicio_act));
	    
		
		// STEP 4 ------------------------------------------
	    float f_proximidad <- factor_proximidad(distancia_inicio, distancia_destino);
		//write "[STEP 4] f_proximidad " + f_proximidad;
	    
		// STEP 5 ------------------------------------------
		int pasajeros_en_tramo <- 0;
	    
	    loop p over: passengers {
	        int index_destino <- ruta index_of (first(ruta where (each = p.destino[0])));
	        int index_nuevo_inicio <- ruta index_of (first(ruta where (each = nuevo_inicio)));
	        int index_nueva_destino <- ruta index_of (first(ruta where (each = nuevo_destino)));
	
	        // Solo consideramos si el tramo [nuevo_inicio, nueva_destino] está entre su trayecto
	        if index_destino > index_nuevo_inicio and index_destino <= index_nueva_destino {
	            pasajeros_en_tramo <- pasajeros_en_tramo + 1;
	        }
	    }
	    
	   // write "[STEP 5] Pasajeros afectados por el tramo nuevo " + pasajeros_en_tramo;
	    
		// STEP 6 ------------------------------------------
		int pasajeros_beneficiados <- 0;
	
		if not nuevo_inicio_en_ruta or not nueva_destino_en_ruta {
			loop p over: passengers {
				if (p.destino[0] = nuevo_destino and not nueva_destino_en_ruta) or (p.destino[0] = nuevo_inicio and not nuevo_inicio_en_ruta) {
					pasajeros_beneficiados <- pasajeros_beneficiados + 1;
				}
			}
		}
		
	    //write "[STEP 6] Pasajeros beneficiados " + pasajeros_beneficiados;

	    // --- Definimos utilidad ---
	    utilidad <- (f_pertenencia) + 
	    			(f_cercania * f_capacidad) + 
	    			(1 / (1 + distancia_inicio_act)) + 
	    			(f_proximidad) + 
	    			(f_cercania * pasajeros_en_tramo) +
	    			(pasajeros_beneficiados);
	
		//write "[FINAL] UTILIDAD " + utilidad + "\n";
		
	    return utilidad;
	}
	
	
	// -------------------
		
	reflex receive_accept when: !empty(accept_proposals) {
        // Protocolo 1: Notificación parada saturada
        message propuesta_aceptada <- accept_proposals[0];
		list content <- list(propuesta_aceptada.contents);
		
		bus_stop nuevo_inicio <- bus_stop(content[0]);
		bus_stop nuevo_destino <- bus_stop(content[1]);
		
		bool nuevo_inicio_en_ruta <- nuevo_inicio in ruta;
	    bool nueva_destino_en_ruta <- nuevo_destino in ruta;

	    // STEP 2 ------------------------------------------
		if not nuevo_inicio_en_ruta {
       		int mejor_posicion <- 0;
	        float menor_distancia <- 999999;
	
	        loop i from: 0 to:(length(ruta) - 2) {
	            float d1 <- distance_to(ruta[i].location, nuevo_inicio.location);
	            float d2 <- distance_to(ruta[i+1].location, nuevo_inicio.location);
	            float total <- d1 + d2;
	
	            if total < menor_distancia {
	                menor_distancia <- total;
	                mejor_posicion <- i + 1;
	            }
	        }
	        
	        list<bus_stop> parte_antes <- ruta[0::mejor_posicion];
			list<bus_stop> parte_despues <- ruta[mejor_posicion::length(ruta)];
			ruta <- parte_antes + [nuevo_inicio] + parte_despues;   
		}
	
	    if not nueva_destino_en_ruta {
	        int mejor_posicion <- 0;
	        float menor_distancia <- 999999;
	
	        loop i from: 0 to:(length(ruta) - 2) {
	            float d1 <- distance_to(ruta[i].location, nuevo_destino.location);
	            float d2 <- distance_to(ruta[i+1].location, nuevo_destino.location);
	            float total <- d1 + d2;
	
	            if total < menor_distancia {
	                menor_distancia <- total;
	                mejor_posicion <- i + 1;
	            }
	        }
       		list<bus_stop> parte_antes <- ruta[0::mejor_posicion];
			list<bus_stop> parte_despues <- ruta[mejor_posicion::length(ruta)];
			ruta <- parte_antes + [nuevo_destino] + parte_despues;
	    }
		
		write "AYUDA ACEPTADA " + self + " " + linea + " " + propuesta_aceptada;
		logs_ruta_dinamicas << [string(self), time, linea, nuevo_inicio, nuevo_destino] + "\n";
		do inform message: propuesta_aceptada contents: ["[BUS] Ruta dinámica incorporada"];
	}

	// ------------------------------------------------ WORKING IN PROGRESS ----------------------------------------------------
	
	action inform_estimated_time_arrival {
        // Protocolo 6: Notificación de tiempo estimado de llegada
		int max_iteraciones <- min(5, length(ruta));
		
		loop i from: 0 to:(max_iteraciones - 1) {
			float minutos <- calculate_estimated_time_arrival(ruta[i].location);
	      	do start_conversation to: [ruta[i]] protocol: "no-protocol" performative: "inform" contents: ["Estimación de llegada a la parada", linea, self, minutos];
		} 
	}
	
	action registrar_llegada {
		// Protocolo 8: Registro frecuencia del servicio
      	do start_conversation to: [parada_actual] protocol: "no-protocol" performative: "inform" contents: ["Registro servicio", linea, to_military_time(time)];
	} 
	
	reflex receive_propose when: !empty(proposes) {
		message propose <- proposes[0];
		list content <- list(propose.contents);
		
		if content[0] = "Quiero embarcar" {
			// Protocolo 4: Embarque de pasajeros
			respuestas_esperadas <- respuestas_esperadas - 1;
			
			if plazas_disponibles > 0 {
				plazas_disponibles <- plazas_disponibles - 1;
    			passengers << propose.sender;
    			
                logs << ["SUBE",string(self), propose.sender, parada_actual, parada_actual.name, content[1], ruta] + "\n";
                
    			//write "BUS "+ self + " Acepta " + propose.sender;
				do accept_proposal message: propose contents: propose.contents;
			} else {
				//write "BUS "+ self + " Rechaza " + propose.sender;
				do reject_proposal message: propose contents: propose.contents;
			}
			
			//write "BUS " + self + " respuestas " + respuestas_esperadas;
			
			if respuestas_esperadas = 0 {
				do add_belief(embarque_completo);
			}
			
		}
	}
	
	reflex receive_refuses when: !empty(refuses) {
		message rechazos <- refuses[0];
		list content <- list(rechazos.contents);
		
		if content[0] = "No quiero embarcar" {
			// Protocolo 4: Embarque de pasajeros
			respuestas_esperadas <- respuestas_esperadas - 1;
			
			//write "BUS "+ self + " pasajero rechaza " + rechazos.sender;
			//write "BUS " + self + " respuestas " + respuestas_esperadas;
			
			if respuestas_esperadas = 0 {
				do add_belief(embarque_completo);
			}
		}
	}
    
    reflex block_bus_stop when: siguiente_parada.bloqueada {
		// Protocolo 5: Notificación parada inaccesible
		do start_conversation to: [siguiente_parada] protocol: "no-protocol" performative: "inform" contents: ["Parada inaccesible", siguiente_parada, ruta[0].location];

	    loop p over: passengers {
	        if (p.destino[0].location = interseccion_siguiente_parada.location) {
	        	do start_conversation to: [p] protocol: "no-protocol" performative: "inform" contents: ["Destino inaccesible", siguiente_parada, ruta[0]];        
			}
	    }
    }
    
	reflex receive_inform when: !empty(informs) {
		message info <- informs[0];	
		do end_conversation message: info contents: [];
	}
	
   	// -------------------------------------------------------------- ASPECTO --------------------------------------------------------------
	aspect base {
       if !has_belief(ruta_finalizada) {
			draw image("/Users/felipe/PycharmProjects/GeoJsonMapGenerator/images/autobus.png") size: {14, 42} rotate: heading + 90;
    	}
    }
}


// -------------------------------------------------------------------------------------------------------------------------------------
// ------------------------------------------------------------- PASAJERO --------------------------------------------------------------
// -------------------------------------------------------------------------------------------------------------------------------------
species passenger skills: [fipa] control: simple_bdi {
    // ------------------------------------------------------------ CREENCIAS --------------------------------------------------------------
    predicate en_bus <- new_predicate("en_bus");
    predicate esperando_bus <- new_predicate("esperando_bus");
	predicate bus_disponible <- new_predicate("bus_disponible");
	predicate bus_seleccionado <- new_predicate("bus_seleccionado");	
	predicate destino_alcanzado <- new_predicate("destino_alcanzado");	
	predicate esperando_transbordo <- new_predicate("esperando_transbordo");
	predicate parada_llegada_notificada <- new_predicate("parada_llegada_notificada");
	predicate parada_embarque_notificado <- new_predicate("parada_embarque_notificado");

    string hora_inicio; // Indica en la que el pasajero se ha generado.
    
    bus bus_actual; // Identificador del bus en el que el pasajero se encuentra.
    
    bus_stop parada_inicial; // Indica la parada de autobús en la que se ha generado al pasajero.
    bus_stop parada_actual; // Indica la parada de autobús en la que se encuentra el pasajero.
    bus_stop ultimo_destino; // Almacena el ultimo destino de un pasajero.
    list<bus_stop> destino; // Listado con el destino del pasajero, en caso de tener que hacer transbordo se almacenará más de un destino.
    
    list<string> lineas_directas; // Listado de lineas validas para alcanzar el siguiente destino.
    
    map<string, map<bus, float>> tiempos_estimados_llegada; // Listado de las estimaciones temporales de los próximos buses que pasarán por la parada actual.
    
    float tiempo_espera <- 0.0#s; 
    float tiempo_viaje <- 0.0#s; 
    float tiempo_transbordo <- 0.0#s; 
    float tiempo_total <- 0.0#s;
    
    // -------------------------------------------------------------- DESEOS ---------------------------------------------------------------
    predicate llegada_parada <- new_predicate("llegada_parada");
    predicate embarcar <- new_predicate("embarcar");
	
    // --------------------------------------------------------- INICIALIZACIÓN ------------------------------------------------------------
    init{
    	logs_passengers_generation << [string(self), hora_inicio, parada_inicial.name, parada_inicial get "ref", destino[0].name, destino[0] get "ref"] + "\n";
    	ultimo_destino <- destino[0];
    	parada_actual <- parada_inicial;
        do calculate_valid_direct_lines;
    	do add_belief(esperando_bus);
    }
    
	// -------------------------------------------------------------- REGLAS ---------------------------------------------------------------
    // Regla 1: Cuando estoy esperando bus y no he notificado a la parada mi llegada
    rule belief: esperando_bus when: not has_belief(parada_llegada_notificada) and not has_belief(en_bus) new_desire: llegada_parada;
    
    // Regla 2: Cuando encuentro un bus que me sirve
    rule beliefs: [bus_disponible, bus_seleccionado, en_bus] new_desire: embarcar;
	
	// ------------------------------------------------------ INTENCIONES / PLANES ---------------------------------------------------------
	plan llegada_parada intention: llegada_parada {
        parada_actual <- first(bus_stop where (each.location = self.location));
        if parada_actual != nil {
        	// Protocolo 2: Notificación llegada a parada
            parada_actual.destino_pasajeros[destino[0]] <- parada_actual.destino_pasajeros[destino[0]] + 1;
            do start_conversation to: [parada_actual] protocol: "no-protocol" performative: "inform" contents: ["Llegada a la parada", destino[0]];
            ask parada_actual { do update_passengers; }
            do add_belief(parada_llegada_notificada);
            
            // Protocolo 7: Solicitud de tiempos estimados de llegada
            do request_estimated_time_arrival;
        }

        do remove_desire(llegada_parada);
        do remove_intention(llegada_parada);
    }
    
    plan embarcar intention: embarcar {
    	if !has_belief(parada_embarque_notificado) {
	        // Protocolo 9: Notificación abandono de parada
	        parada_actual.destino_pasajeros[ultimo_destino] <- parada_actual.destino_pasajeros[ultimo_destino] - 1;
	        ultimo_destino <- destino[0];
	        do start_conversation to: [parada_actual] protocol: "no-protocol" performative: "inform" contents: ["Abandono parada"];
	        ask parada_actual { do update_passengers; }
	        do add_belief(parada_embarque_notificado);
    	}

		do remove_belief(bus_disponible);
		do remove_belief(bus_seleccionado);
		
        do remove_desire(embarcar);
        do remove_intention(embarcar);
    }
	
	// ------------------------------------------------------------- ACCIONES --------------------------------------------------------------
    reflex tiempo_espera when: has_belief(esperando_bus){
    	tiempo_espera <- tiempo_espera + step;
    }
    
    reflex tiempo_transporte when: has_belief(en_bus) {
    	tiempo_viaje <- tiempo_viaje + step;
    }
    
    reflex tiempo_transbordo when: has_belief(esperando_transbordo){
    	tiempo_transbordo <- tiempo_transbordo + step;
    }
    
    reflex tiempo_total when: has_belief(destino_alcanzado) {
    	tiempo_total <- tiempo_espera + tiempo_viaje;
    }
    
	action calculate_valid_direct_lines {
	    loop l over: lineas_group.keys {		
	        if (destino[0] in lineas_group[l]) and (parada_actual in lineas_group[l]) {
	        	
	        	int pos_actual <- lineas_group[l] index_of parada_actual;
            	int pos_destino <- lineas_group[l] index_of destino[0];
            	
	        	if pos_destino > pos_actual {
	                lineas_directas << l;
            	}
	        }
	    }
	}	
	
    // ------------------------------------------------ PROTOCOLOS DE COMUNICACIÓN FIPA ----------------------------------------------------
	reflex receive_cfps when: !empty(cfps) {
		message propose <- cfps[0];
		list content <- list(propose.contents);
		
		if content[0] = "¿Quieres subir?" {
			// Protocolo 4: Embarque de pasajeros
			do add_belief(bus_disponible);
		
			if destino[0] in content[1]{
				do add_belief(bus_seleccionado);
				//write "BUS ME LLEVA DIRECTO AL DESTINO " + destino[0];
				
			} else if bus_actual != content[3] {
				bool linea_directa_disponible <- false;
				
				if not empty(lineas_directas) {
		    		loop l over: lineas_directas {
					    if (parada_actual.tiempos_estimados_llegada.keys contains l) and (parada_actual.tiempos_estimados_llegada[l] != nil) {
					    	//write "PASAJERO DECIDE ESPERAR - OTRO BUS " + l + " ME LLEVA DIRECTO AL DESTINO " + destino[0];
					    	linea_directa_disponible <- true;
					    	break;
			    		}
			   		}
	    
				}
				
				if !linea_directa_disponible {
					list<map<string, bus_stop>> valid_transfers <- [];
					 
				    // 1. Encontrar todas las líneas que pasan por el destino
				    list<string> lines_to_dest <- lineas_group.keys where (destino[0] in lineas_group[each]);
				    
				    // 2. Buscar combinaciones válidas
				    int pos_current_in_line1 <- lineas_group[content[2]] index_of parada_actual;
			        
			        loop line2 over: lines_to_dest where (each != content[2]) {
			            int pos_dest_in_line2 <- last_index_of(lineas_group[line2], destino[0]);
			            
			            // write "MI LINEA " + content[2] + " LINEAS A DESTINO " + lines_to_dest;
			            
			            // Buscar paradas comunes donde se pueda hacer transbordo
			            loop stop over: lineas_group[content[2]] {
			            	if stop in lineas_group[line2] {
			            		int pos_transfer_in_line1 <- lineas_group[content[2]] index_of stop;
				                int pos_transfer_in_line2 <- lineas_group[line2] index_of stop;
				                
				                // Verificar dirección correcta en ambas líneas
				                bool valid_line1_direction <- pos_transfer_in_line1 > pos_current_in_line1;
				                bool valid_line2_direction <- pos_dest_in_line2 > pos_transfer_in_line2;
				                
				                // write "DESTINO " + destino[0] + destino[0] get "ref" + " TRANSBORDO " + stop + stop get "ref" + " - 1" + valid_line1_direction + "2" + valid_line2_direction;
				                
				                if (valid_line1_direction and valid_line2_direction) {
				                    valid_transfers << [
				                        "line1":: content[2],
				                        "line2":: line2,
				                        "transfer_stop":: stop,
				                        "stops_before_transfer":: pos_transfer_in_line1 - pos_current_in_line1,
				                        "stops_after_transfer":: pos_dest_in_line2 - pos_transfer_in_line2,
				                        "total_stops":: (pos_transfer_in_line1 - pos_current_in_line1) + (pos_dest_in_line2 - pos_transfer_in_line2)
				                    ];
				                }
			            	}
			            }
					}
				    
				    if (not empty(valid_transfers)) {
					    // Ordenar por menor número total de paradas
				    	valid_transfers <- valid_transfers sort_by (each["total_stops"]);
				    	
				        /*write "Opciones de transbordo válidas:";
				        loop transfer over: valid_transfers {
				            write "1. Tomar " + transfer["line1"] + " desde " + parada_actual + 
				                  " hasta " + transfer["transfer_stop"] + " (" + transfer["stops_before_transfer"] + " paradas)" +
				                  "\n2. Cambiar a " + transfer["line2"] + " hasta " + destino[0] + 
				                  " (" + transfer["stops_after_transfer"] + " paradas)\n" +
				                  "Total: " + transfer["total_stops"] + " paradas\n";
				        }*/
				        
				        //write "TRANSBORDO CALCULADO";
				        				        
				        destino <- [bus_stop(valid_transfers[0]["transfer_stop"])] + destino;
						do add_belief(bus_seleccionado);
				    } else {
				        //write "No se encontraron rutas con transbordo válidas.";
				    }					
				}
			}
			
			if has_belief(bus_seleccionado) and (propose.sender != bus_actual) and not has_belief(en_bus) {
				write "Pasajero " + self + " SI quiere." + destino[0] + destino[0].name + destino;
				do propose message: propose contents: ["Quiero embarcar", destino];
			} else {
				write "Pasajero " + self + " BUS " +  propose.sender + " NO quiere su destino es " + destino[0] + " " + destino[0] get "ref" + " " + destino[0].name + destino;
				do refuse message: propose contents: ["No quiero embarcar"];
			}
		}
	}
	
	reflex receive_accept when: !empty(accept_proposals) {
        // Protocolo 4: Embarque de pasajeros
        message propuesta_aceptada <- accept_proposals[0];
		list content <- list(propuesta_aceptada.contents);
		
		bus_actual <- propuesta_aceptada.sender;
		
		self.location <- (0,0);	
		
    	do remove_belief(esperando_bus);
		do remove_belief(esperando_transbordo);
		do remove_belief(parada_llegada_notificada);
		do remove_belief(parada_embarque_notificado);
		
    	do add_belief(en_bus);
	}

	action request_estimated_time_arrival {
		// Protocolo 7: Solicitud de tiempos estimados de llegada
		do start_conversation to: [parada_actual] protocol: "fipa-request" performative: "request" contents: ["Solicitud E.T.A.s"];
	}
	
	reflex receive_agrees when: !empty(agrees){
		message info <- agrees[0];
		list content <- list(info.contents);
		
		if content[0] = "Solicitud E.T.A.s" {
			// Protocolo 7: Solicitud de tiempos estimados de llegada
			tiempos_estimados_llegada <- content[1];
		}
	}
	
	reflex receive_inform when: !empty(informs) {
		message info <- informs[0];
		list content <- list(info.contents);

		if content[0] = "Transbordo alcanzado" {
			// Protocolo 3: Desembarque de pasajeros
			self.location <- content[2];
			destino <- destino - destino[0];      
		 	do calculate_valid_direct_lines;  		
		 	
    		do remove_belief(en_bus);			
			do remove_belief(parada_llegada_notificada);
			do remove_belief(parada_embarque_notificado);
			
	 		do add_belief(esperando_bus);
	    	do add_belief(esperando_transbordo);
	 	
	 	} else if content[0] = "Destino alcanzado" {
	 		// Protocolo 3: Desembarque de pasajeros
        	do remove_belief(en_bus);
	 		do add_belief(destino_alcanzado);
	 		
		} else if content[0] = "Destino inaccesible" {
			// Protocolo 5: Notificación parada inaccesible
			destino[0] <- content[2];
		} else if content[0] = "Inicio inaccesible" {
			// Protocolo 5: Notificación parada inaccesible
			self.location <- content[2];
			do remove_belief(parada_llegada_notificada);
		} 
		
		do end_conversation message: info contents: [];
	}
	
	// -------------------------------------------------------------- ASPECTO --------------------------------------------------------------
    aspect base {
    	if has_belief(esperando_bus) {
    		 draw circle(2) color: #orange; // Representación visual del pasajero
    	}
    }
}


experiment simulacion type: gui {
    output synchronized: false {
        display map type: 3d background: rgb(242, 243, 244) {
		    species road aspect: base;
		    species building aspect: base;
		    species bus_stop aspect: base;
		    species bus aspect: base;
		    species passenger aspect: base;
        }
    }
}