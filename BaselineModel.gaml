/**
* Name: Modelobase
* Based on the internal empty template. 
* Author: A. Felipe Camacho Martínez
* Tags: UC3M
*/

model BaselineModel


global {
	// Carga de archivos GeoJSON
    file roads_file <- file("/Users/felipe/PycharmProjects/GeoJsonMapGenerator/geojson/aristas.geojson");
    file nodes_file <- file("/Users/felipe/PycharmProjects/GeoJsonMapGenerator/geojson/nodos.geojson");
    file building_file <- file("/Users/felipe/PycharmProjects/GeoJsonMapGenerator/geojson/edificios.geojson");
    file bus_stop_file <- file("/Users/felipe/PycharmProjects/GeoJsonMapGenerator/geojson/paradas.geojson");
    geometry shape <- envelope(roads_file) #m;
    graph road_network;
    
    // Variables globales
    float step <- 1#s;
    float ini_time <- 3600#s; // Como la demanda varía en función de la hora, variable para fijar la hora de inicio
	float max_time <- 3600#s; // 1 hora 3600s
	
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
	
	list stops_651A <- ['06230', '09094', '07304', '06232', '06233', '06234', '06235', '06236', '06215', '06237', '06216', '06176', '06240', '11859', '11860', '11862', '11865', '11867', '09409', '11855', '10491', '18613', '06177', '12995'];
	list stops_651B <- ['06244', '18072', '18612', '11835', '11854', '11856', '11868', '11866', '11861', '06518', '06424', '06205', '06249', '06212', '06250', '06251', '06252', '06253', '06254'];
	list stops_652A <- ['06230', '09094', '07304', '06232', '06233', '06234', '06235', '06236', '06178', '11857', '11858', '17330', '17332', '17334', '18882', '20611'];
	list stops_652B <- ['20611', '17336', '17335', '17333', '17331', '06242', '06203', '06250', '06251', '06252', '06253', '06254', '07305', '09093', '06256'];
	list stops_l1 <- ['17923', '17685', '11385', '11417', '12747', '12994', '12992', '18070', '12990', '12991', '12993', '12748', '18073', '18612', '11835', '11854', '11858', '17330', '18498', '11861', '06518', '06424', '06205', '17742', '12500', '12504', '06251', '06252', '06253', '06254', '13003', '17700', '12905', '12906', '12907', '09407', '12995', '11421', '08792', '12066', '09368', '08790', '08788', '12679', '15188', '17270', '17724', '17925', '17923'];
	list stops_l2 <- ['17924', '17683', '17725', '17721', '17269', '15189', '08787', '08789', '09368', '12067', '08791', '11420', '06244', '12271', '06429', '12908', '12909', '12910', '17699', '16386', '06232', '06233', '06234', '06235', '12503', '12499', '17743', '06176', '06240', '11859', '11860', '18497', '17331', '06242', '09409', '11855', '10491', '18613', '18071', '06245', '08796', '12994', '12992', '18070', '12990', '12991', '12993', '12989', '11418', '11386', '17684', '17924'];
	list all_routes <- (stops_651A + stops_651B + stops_652A + stops_652B + stops_l1 + stops_l2);
	list<bus_stop> sub_bus_stops <- [];
    		
    map<string, list<bus_stop>> lineas_group;

	float frecuency_651 <- 601#s; // 10 minutos
	float frecuency_652 <- 901#s; // 15 minutos
	float frecuency_l <- 1801#s; // 30 minutos
	
	float time_651 <- 0#s;
	float time_652 <- 0#s;
	float time_l <- 0#s;
	
	// --------------------------------------------- MODELO GENERACIÓN DE DEMANDA DE PASAJEROS ---------------------------------------------
	// Variables para la generación de la demanda de pasajeros
	float pi <- 3.141592653589793;
	float lambda_base <- 1.0; // Tasa base de generación de pasajeros (λ_0)
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
    
    map<string, map<string, string>> eiijemplo <- [
    	"Pasajero" :: ["06236"::"S"]
    ];
    
    int frecuency_passengers <- 1201#s; // 20 minutos
    float time_passengers <- 0#s;
	
	// TEMPORAL PRUEBAS
	bool comentarios <- false;
	bool ini <- true;
	bool pruebas <- true;
	
    // ------------------------------------------------------------- PREDICADOS ------------------------------------------------------------
    predicate aborda <- new_predicate("aborda");
	predicate bus_lleno <- new_predicate("bus_lleno");
    predicate carretera_congestionada <- new_predicate("carretera_congestionada");
	predicate carretera_bloqueada <- new_predicate("carretera_bloqueada");
	predicate circula_por <- new_predicate("circula_por");
    predicate desembarca <- new_predicate("desembarca");
	predicate destino_alcanzado <- new_predicate("destino_alcanzado");
	predicate destino_asignado <- new_predicate("destino_asignado");
    predicate informar_eventos <- new_predicate("informar_eventos");
	predicate omite_parada <- new_predicate("omite_parada");
	predicate parada_saturada <- new_predicate("parada_saturada");
	predicate pasajero_esperando <- new_predicate("pasajero_esperando");
	predicate ruta_asignada <- new_predicate("ruta_asignada");
	predicate ruta_finalizada <- new_predicate("ruta_finalizada");
	predicate se_detiene_en <- new_predicate("se_detiene_en");
	predicate transbordo <- new_predicate("transbordo");
	
	// --------------------------------------------------------------- LOGS  ---------------------------------------------------------------
	list<list> logs_bus_generation;
	list<list> logs_bus_results;
	
	list<list> logs_passengers_generation;
	list<list> logs_passengers_results;
    
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
      	logs_bus_generation << ["Bus", "linea", "hora"] + "\n";
      	logs_bus_results << ["Bus", "linea", "hora", "ruta_finalizada", "num_pasajeros"] + "\n";
       
        logs_passengers_generation << ["Pasajero", "hora", "inicio", "ref_inicio", "destino", "ref_destino"] + "\n";
        logs_passengers_results << ["Pasajero", "tiempo_espera", "tiempo_viaje", "tiempo_transbordo", "tiempo_total"] + "\n";
		
		if !pruebas{
			create bus with: [ruta: route_651A, hora_inicio: to_military_time(time), linea: "651A", location: start_point_madrid.location] number: 1;
	        create bus with: [ruta: route_651B, hora_inicio: to_military_time(time), linea: "651B", location: start_point_macas.location] number: 1;
	        create bus with: [ruta: route_652A, hora_inicio: to_military_time(time), linea: "652A", location: start_point_madrid.location] number: 1;
	        create bus with: [ruta: route_652B, hora_inicio: to_military_time(time), linea: "652B", location: start_point_gp.location] number: 1;
	        create bus with: [ruta: route_l1, hora_inicio: to_military_time(time), linea: "l1", location: start_point_l.location] number: 1;
	        create bus with: [ruta: route_l2, hora_inicio: to_military_time(time), linea: "l2", location: start_point_l2.location] number: 1;
		} else {
			create bus with: [ruta: route_l1, hora_inicio: to_military_time(time), linea: "l1", location: start_point_madrid.location] number: 1;
			create bus with: [ruta: route_651B, hora_inicio: to_military_time(time), linea: "651B", location: start_point_madrid.location] number: 1;
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
	
    reflex create_buses when: pruebas {    	
        if (time - time_651 >= frecuency_651) {
            create bus with: [ruta: route_651A, hora_inicio: to_military_time(time), linea: "651A", location: start_point_madrid.location] number: 1;
            create bus with: [ruta: route_651B, hora_inicio: to_military_time(time), linea: "651B", location: start_point_macas.location] number: 1;
            time_651 <- time;
        }
        if (time - time_652 >= frecuency_652) {
            create bus with: [ruta: route_652A, hora_inicio: to_military_time(time), linea: "652A", location: start_point_madrid.location] number: 1;
            create bus with: [ruta: route_652B,hora_inicio: to_military_time(time), linea: "652B", location: start_point_gp.location] number: 1;
            time_652 <- time;
        }
        if (time - time_l >= frecuency_l) {
            create bus with: [ruta: route_l1, hora_inicio: to_military_time(time), linea: "l1", location: start_point_l.location] number: 1;
            create bus with: [ruta: route_l2, hora_inicio: to_military_time(time), linea: "l2", location: start_point_l2.location] number: 1;
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
    	bool block <- flip(0.01); 
        if (block) {
			road calle_cortada <- one_of(road_network.edges);
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
    	bool traffic <- flip(0.05); 
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
       
	    event <- one_of ([1,1,1,1,1,1,1,1,2,2]); // Event
	    
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
		if mod(int(time), frecuency_passengers) = 0 {
			int generados <- assemble_passenger((time/60)/100);
			
			write "[HORA]: segundos " + time + " minutos " + (time/60) + " en horas " + to_military_time(time) + " se han generado un total de " + generados + " pasajeros.";
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
    		logs_bus_results << [string(self), self.linea, h, has_belief(ruta_finalizada), (self.capacidad_maxima - self.plazas_disponibles)] + "\n";
    		//write "[INFO] "  + string(self) + " Ha finalizado su ruta con " + (self.capacidad_maxima - self.plazas_disponibles) + " pasajeros.";
    	}

    	ask passenger {
    		logs_passengers_results << [string(self), self.tiempo_espera, self.tiempo_viaje, self.tiempo_transbordo, self.tiempo_total] + "\n";
    		//write "[TIEMPOS] " + string(self) + " tiempos de espera: " + self.tiempo_espera + " viaje: " + self.tiempo_viaje + " transbordo: " + self.tiempo_transbordo +  " total: " + self.tiempo_total;
		}
		
		save logs_bus_generation to: "exports/bus_generation_basic.csv"; 
		save logs_bus_results to: "exports/bus_results_basic.csv";
				
		save logs_passengers_generation to: "exports/passengers_generation_basic.csv"; 
		save logs_passengers_results to: "exports/passengers_results_basic.csv"; 
		
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
	bool saturada <- false; // Booleano que indica si una parada está saturada debido al número de pasajeros que se encuentra en ella.
	bool ocupada <- false; // Booleano que indica si la parada está siendo utilizada por un bus para operaciones de embarque o desembarque.
	int total_pasajeros <- 0;
	map<bus_stop, int> destino_pasajeros; // Agrupación del número de pasajeros por destino en la parada.
	list<passenger> pasajeros_transbordo; // Listado de los pasajeros que se encuentran en la parada haciendo transbordo.
	int alerta_saturacion <- 20;

	// --------------------------------------------------------- PROTOCOLOS FIPA -----------------------------------------------------------
	reflex receive_inform when: !empty(informs) {
		message info <- informs[0];			
		do end_conversation message: info contents: [];
	}

    aspect base {
        draw image("/Users/felipe/PycharmProjects/GeoJsonMapGenerator/images/parada.png") size: {10, 15};
    }
}

// -------------------------------------------------------------------------------------------------------------------------------------
// --------------------------------------------------------------- BUS -----------------------------------------------------------------
// -------------------------------------------------------------------------------------------------------------------------------------
species bus skills: [driving, fipa] control: simple_bdi {
	string request_subir <- "subir";
	string hora_inicio;
	
    // -------------------------------------------------------------- HECHOS ---------------------------------------------------------------
	int capacidad_maxima;
    int plazas_disponibles;
	
	// --------------------------------------------------------- CREENCIAS INTERNAS --------------------------------------------------------
    bus_stop siguiente_parada;	
    bus_stop parada_anterior;
    float distancia_siguiente_parada <- 0.0;
    bool ruta_calculada <- false;	
    bool ultima_parada <- false;
    
	// --------------------------------------------------------- CREENCIAS EXTERNAS --------------------------------------------------------
	list<bus_stop> ruta;
	string linea;
    intersection interseccion_siguiente_parada;
    intersection interseccion;
    list<passenger> passengers <- []; // Pasajeros en el autobús
    list<passenger> waiting_passengers;
	bool esperando <- false;
	int maxima_espera <- 0;
    
    // EVENTOS CARRETERAS, listado de los eventos activos
    // NÚMERO DE PASAJEROS EN LA SIGUIENTE PARADA (HAY PASAJEROS)
    // PASAJERO A RECOGER, NOMBRE Y PARADA (HAY PASAJEROS A DEJAR)
    // DEJAR PASAJERO, NOMBRE EN PLAN PASAJERO_EN, Y PARADA (PASAJERO_EN)
    
    
    // -------------------------------------------------------------- DESEOS ---------------------------------------------------------------
    // En base a sus creencias el agente genera deseos
    bool aborda_aux;
    bool desembarcar;
    
    // DESEO COMPLETAR RUTA
    // en carretera, en parada,
    // CREENCIA PROXIMA PARADA, RUTA CALCULADA, EVENTOS, PASAJEROS, TENGO QUE PARAR, PLAZAS DISPONIBLES, ULTIMA PARADA, PARADA COMPLETADA 
	
	
	// PLAN CONDUCIR, (VAMOS CHECKEANDO EL ESTADO DE LA CARRETERA POR SI EVENTOS) EN PARADA (RECOGER Y DEJAR PASAJEROS
	// INTENCION CONDUCIR
	// estoy lleno creemncia
	// CREENCIA DE PARADA SATURADA, CREENCIA EVENTOS, creencia estoy en parada, CREENCIA ESTOY DISPONIBLE PARA DESPUES
	
	// PLAN ACABAR RUTA, PLAN CONDUCIR, PLAN RECOGER, PLAN ELEGIR PROXIMA PARADA
	
	

    init {
        vehicle_length <- 12 #m; // Longitud de un autobús
        max_speed <- 100 #km / #h; // Velocidad máxima permitida
        max_acceleration <- 1.92; // Aceleración
        capacidad_maxima <- 86; 
        plazas_disponibles <- capacidad_maxima;
        
	    logs_bus_generation << [string(self), linea, hora_inicio] + "\n";
    }
	
	reflex select_next_path when: current_path = nil and not ruta_calculada and not ultima_parada { 
	    siguiente_parada <- ruta[0];
	    
        interseccion_siguiente_parada <- find_intersection();        
        
        if (interseccion_siguiente_parada != nil and interseccion_siguiente_parada != self.location) {
			do compute_path graph: road_network target: interseccion_siguiente_parada;

            if (length(ruta) = 1) {
                ultima_parada <- true;
            } else {
            	ruta <- ruta - ruta[0];
            }
        	ruta_calculada <- true;
        }
        //write "[BUS] " + self + "/" + linea + " nuevo destino " + siguiente_parada + "/" + siguiente_parada.name + "\n";
	}
	
	intersection find_intersection{
		intersection aux_destino;
		float aux_distancia;
        loop f over: intersection as list {
            aux_distancia <- distance_to(f.location, siguiente_parada.shape.location);
            if (aux_distancia = 0) {
				aux_destino <- f;
			}
        }
        return aux_destino;
	}
	
	reflex commute when: current_path != nil or esperando{
        if current_path != nil{
            do drive;	
        }
        
        // distancia_siguiente_parada <- distance_to(self.location, interseccion_siguiente_parada.location);
        if (interseccion_siguiente_parada.location = self.location){
        	
        	if (!siguiente_parada.ocupada){
	        	
	        	if !ultima_parada{
	        		//write "[BUS] " + self + "/" + linea + " ha OCUPADO la parada " + siguiente_parada + "/" + siguiente_parada.name + "\n";
					
	        		siguiente_parada.ocupada <- true; // Bloqueo la parada
		        	parada_anterior <- siguiente_parada;
		        	esperando <- false;
		        	ruta_calculada <-false;
					desembarcar <- true;
					if (self.plazas_disponibles > 0){
						aborda_aux <- true;				
					}
	        	} else {
	        		desembarcar <- true;
	        		do add_belief(ruta_finalizada);
	        	}	
        	} else {
        		esperando <- true;
        		maxima_espera <- maxima_espera + 1;
        		
        		if maxima_espera > 5 {
        			write "maxima espera alcanzada";
        			parada_anterior <- siguiente_parada;
		        	esperando <- false;
		        	ruta_calculada <-false;
		        	desembarcar <- true;
		        	maxima_espera <- 0;
		        }
        		
        		//write "[PROBLEMA] " + self + "/" + linea + " ESPERANDO la parada " + siguiente_parada + "/" + siguiente_parada.name;
        	}
        }
    }

	// ------------------------------------------------------ INTENCIONES / PLANES --------------------------------------------------------- a PARTIR DE LOS DESEOS selecciona algunos para convertirlos en intenciones los planes son agrupaciones de acciones
	// -------------------------------------------------------------- REGLAS ---------------------------------------------------------------
	// --------------------------------------------------------- PROTOCOLOS FIPA -----------------------------------------------------------
    
    reflex let_passengers_off when: desembarcar{
        list<passenger> passengers_to_remove <- [];
        
	    loop p over: passengers {
	        if (p.destino[0].location = interseccion_siguiente_parada.location) {
			    passengers_to_remove << p;
	            plazas_disponibles <- plazas_disponibles + 1;
	            
	            if length(p.destino)>1{
	            	do start_conversation to: [p] protocol: "no-protocol" performative: "inform" contents: ["Transbordo alcanzado", p.destino[0]];
	            	//write "[PASAJERO-TRANSBORDO] " + p + " ha bajado del autobús " + self + " ruta " + linea + " en la parada " + siguiente_parada + "/" + siguiente_parada.name + " siguiente destino " + p.destino[1];
	            	
	            	ask p{
	            		p.location <- p.destino[0].location;
	            		p.notificado_parada <- false;	            		
		            	do remove_belief(aborda);
		            	do add_belief(transbordo);
	        	 		do add_belief(pasajero_esperando);
	            		p.destino <- p.destino - p.destino[0];
	            	}
	            } else {
					do start_conversation to: [p] protocol: "no-protocol" performative: "inform" contents: ["Destino alcanzado", p.destino[0]];
					//write "[PASAJERO-BAJA] " + p + " ha bajado del autobús " + self + " ruta " + linea + " en la parada " + siguiente_parada + "/" + siguiente_parada.name;
	            
	            	ask p{
            			do remove_belief(transbordo);
		            	do remove_belief(aborda);
	        	 		do add_belief(destino_alcanzado);
	            	}
	            }
	        }
	    }
	    
     	passengers <- passengers - passengers_to_remove;
     	desembarcar <- false;
    }
    
    reflex propose_boarding_passengers when: aborda_aux{
    	waiting_passengers <- passenger overlapping (interseccion_siguiente_parada.location);
    	
    	if not empty(waiting_passengers){
    		write "[BUS] " + self + "/" + linea + " en " + parada_anterior + "/" + parada_anterior.name + " Pasajeros " + length(waiting_passengers) + " Plazas dispo " + plazas_disponibles;
    	}
    	
        loop p over: waiting_passengers {
        	// IF PLAZAS DISPONIBLES CUBR E TODA LA DEMANDA DE WAITING PASSENGER HACER CUT AAQUI PORQUE CREO QUE ESTA DANDO PROBLEMAS
	    	do start_conversation to: [p] protocol: "fipa-propose" performative: "propose" contents: [request_subir, ruta, linea, self];
	        //write "Started new conversation with " + p + "\n";     		
        }
        
		if empty(waiting_passengers) {
			parada_anterior.ocupada <- false; // Desbloqueo la parada
        	//write "[BUS] " + self + "/" + linea + " ha liberado la parada " + parada_anterior + "/" + parada_anterior.name + "\n";
		}        
        
    	aborda_aux <- false;
    }
    
    reflex receive_accept when: !empty(accept_proposals) {
        plazas_disponibles <- plazas_disponibles - 1;
        
    	message propuesta_aceptada <- accept_proposals[0];
    	
    	do add_belief(new_predicate("transporta", ["pasajero"::propuesta_aceptada.sender]));
    		
    	passengers << propuesta_aceptada.sender;
    	
    	passenger h <- propuesta_aceptada.sender;
    	
    	h.notificado_parada <- false;

		//write "Se cierra " + propuesta_aceptada + "\n";
		
    	do end_conversation message: propuesta_aceptada contents: [];
    	
		waiting_passengers <- waiting_passengers - propuesta_aceptada.sender;
		
		if empty(waiting_passengers) {
			parada_anterior.ocupada <- false; // Desbloqueo la parada
        	//write "[BUS] " + self + "/" + linea + " ha liberado la parada " + parada_anterior + "/" + parada_anterior.name + "\n";
		}
    }
    
	reflex receive_reject when: !empty(reject_proposals) {
		message rechazo <- reject_proposals[0];

		//write "Se cierra " + rechazo + "\n";
		
		do end_conversation message: rechazo contents: [];	
		
		waiting_passengers <- waiting_passengers - rechazo.sender;
				
		if empty(waiting_passengers) {
			parada_anterior.ocupada <- false; // Desbloqueo la parada
        	//write "[BUS] " + self + "/" + linea + " ha liberado la parada " + parada_anterior + "/" + parada_anterior.name + "\n";
		}
    }
   
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
    float tiempo_espera <- 0.0#s;
    float tiempo_viaje <- 0.0#s;
    float tiempo_transbordo <- 0.0#s;
    float tiempo_total <- 0.0#s;
    
    string hora_inicio;
    
    bus ultimo_bus;
    bus_stop parada_inicial;
    bus_stop parada_actual;
    bus_stop aux_destino;
    list<bus_stop> destino; // Destino del pasajero
    list auxcon; // ?
    string linea;
    
    
    bool notificado_parada <- false;
    
    init{
    	logs_passengers_generation << [string(self), hora_inicio, parada_inicial.name, parada_inicial get "ref", destino[0].name, destino[0] get "ref"] + "\n";
    	aux_destino <- destino[0];
    	do add_belief(pasajero_esperando);
    }
    
    reflex tiempo_espera when: has_belief(pasajero_esperando){
    	tiempo_espera <- tiempo_espera + step;
    }
    
    reflex tiempo_transporte when: has_belief(aborda) {
    	tiempo_viaje <- tiempo_viaje + step;
    }
    
    reflex tiempo_transbordo when: has_belief(transbordo){
    	tiempo_transbordo <- tiempo_transbordo + step;
    }
    
    reflex tiempo_total when: has_belief(destino_alcanzado) {
    	tiempo_total <- tiempo_espera + tiempo_viaje;
    }
   
    // ------------------------------------------------------ FUNCIONES AUXILIARES ---------------------------------------------------------
	bool calculate_transfer {
		list<string> lineas_validas;

	    loop l over: lineas_group.keys {		
	        if (destino[0] in lineas_group[l]) and (linea != l) {
	            lineas_validas << l;
	        }
	    }
	    
	    if not empty(lineas_validas){
		    list<string> paradas_comunes; list<bus_stop> ruta_linea; list<string> refs_rutalinea;
	    	list<string> refs_auxcon <- auxcon collect (each get 'ref');
		    
		    loop linea over: lineas_validas {
		    	ruta_linea <- lineas_group[linea];
		    	refs_rutalinea <- ruta_linea collect (each get 'ref');
		    	paradas_comunes <-  paradas_comunes + refs_auxcon where (refs_rutalinea contains each);
		    }
	 
		   	if not empty(paradas_comunes) {
			    if comentarios {
			    	write lineas_validas;
					write "ref" + refs_auxcon;
					write "linea" + refs_rutalinea;
					write "Comunes " + paradas_comunes;	
			    }
		   		
				string primer_coincidencia <- first(paradas_comunes where (refs_auxcon contains each));
				destino <- [first(bus_stop where (each get "ref" = primer_coincidencia))] + destino;
				
				return true;
		   	}
	    }
	    return false;
	}
    
    // --------------------------------------------------------- PROTOCOLOS FIPA -----------------------------------------------------------
    reflex inform_bus_stop when: !notificado_parada {
    	if !has_belief(aborda) {
			parada_actual <- first(bus_stop where (each.location = self.location));
			
			if parada_actual != nil {
				parada_actual.destino_pasajeros[destino[0]] <- parada_actual.destino_pasajeros[destino[0]] + 1;
				do start_conversation to: [parada_actual] protocol: "no-protocol" performative: "inform" contents: ["Llego a la parada con destino", destino[0]];
		          	
				notificado_parada <- true;
			}
    	} else {
			parada_actual.destino_pasajeros[aux_destino] <- parada_actual.destino_pasajeros[aux_destino] - 1;
			aux_destino <- destino[0];
			do start_conversation to: [parada_actual] protocol: "no-protocol" performative: "inform" contents: ["Abandono parada"];
			
			notificado_parada <- true;
    	}
	}
	
	reflex receive_propose_messages when: !empty(proposes) {
    	message propose <- proposes[0];
		list content <- list(propose.contents);
		bool puede_subir <- false;

		if content[0] = "subir" {
			if destino[0] in content[1]{
				puede_subir <- true;
			} else {
				auxcon <- content[1];
				linea <- content[2];
				puede_subir <- calculate_transfer();
			}

			if puede_subir and not(has_belief(aborda)) and (propose.sender != ultimo_bus) {
				//write "[PASAJERO-SUBE] " + self + " ubicado en " + inicio + "/" + inicio.name + " SUBE al bus " + propose.sender + " ruta: " + content[2] + " su destino es " + destino[0] + "/" + destino[0].name;
				
				self.location <- (0,0);
				do accept_proposal message: propose contents: propose.contents;
            	do remove_belief(pasajero_esperando);
            	do add_belief(new_predicate("aborda", ["bus"::propose.sender]));
            	ultimo_bus <- propose.sender;
			}else{
				//write "[PASAJERO-NO-SUBE] " + self + " ubicado en " + inicio + "/" + inicio.name  + " NO sube al bus " + propose.sender + " ruta " + content[2] + " su destino es " + destino[0] + "/" + destino[0].name;
				
				do reject_proposal message: propose contents: propose.contents;
			}
		}
	}
	
	reflex receive_inform when: !empty(informs) {
		message info <- informs[0];	
		do end_conversation message: info contents: [];
	}
    
    aspect base {
    	if has_belief(pasajero_esperando) {
    		 draw circle(2) color: #red; // Representación visual del pasajero
    	}
    }
}

experiment simulacion type: batch {
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
