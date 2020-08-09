/* -------------------------------------------------------------------
     File "Core.geo"

     This file is the geometrical description used by GMSH to produce
     the file "Core.msh".
------------------------------------------------------------------- */
r_int_Ind  =  75.e-3 ;
r_ext_Ind  =  100.e-3 ;
h_Ind      =  25.e-3;

r_int_Ind1  =  75.e-3 ;
r_ext_Ind1  =  100.e-3 ;
z0_Ind1      =  35.5e-3;
z1_Ind1      =  85.5e-3;

r_int_Ind2  =  75.e-3 ;
r_ext_Ind2  =  100.e-3 ;
z0_Ind2      =  95.5e-3;
z1_Ind2      = 145.5e-3;

rInt = 400.e-3 ;
rExt = 500.e-3;

s = 1. ;
p0      =  6.e-3 *s;
pCorex  =  2.e-3 *s;
pCorey0 =  4.e-3 *s;
pCorey  =  2.e-3 *s;
pIndx = 1.25e-3 *s;
pIndy = 1.25e-3 *s;
pInd1x = 1.25e-3 *s;
pInd1y = 1.25e-3 *s;
pInt =  6.25e-3 *s;  
pExt = 6.25e-3 *s;

/* Define Discretization for Lines */
nbpt_r = 20;
nbpt_z = 40;
nbpt_glue = 10;

nbpt_r_inf = 30;
nbpt_circum_inf = 80;

nbpt_r_air = 20;
nbpt_rext_air = 40;
nbpt_z_air = 40;

// Points Definition
Point(1) = {0,0,0,pCorey};
//Point(2) = {0,h_Ind,0,pCorey};

// First inducteur
Point(4) = {r_int_Ind,0,0,pIndx};
Point(5) = {r_ext_Ind,0,0,pIndx};
Point(6) = {r_ext_Ind,h_Ind,0,pIndx};
Point(7) = {r_int_Ind,h_Ind,0,pIndx};

Point(10) = {rInt,0,0,pInt};
Point(11) = {rExt,0,0,pInt};
Point(12) = {0,rInt,0,pInt};
Point(13) = {0,rExt,0,pInt};

// Second inducteur

Point(18) = {r_int_Ind1,z0_Ind1,0,pInd1x};
Point(19) = {r_ext_Ind1,z0_Ind1,0,pInd1x};
Point(20) = {r_ext_Ind1,z1_Ind1,0,pInd1x};
Point(21) = {r_int_Ind1,z1_Ind1,0,pInd1x};

// Third inducteur

Point(22) = {r_int_Ind2,z0_Ind2,0,pInd1x};
Point(23) = {r_ext_Ind2,z0_Ind2,0,pInd1x};
Point(24) = {r_ext_Ind2,z1_Ind2,0,pInd1x};
Point(25) = {r_int_Ind2,z1_Ind2,0,pInd1x};

Line(1)  = {1,4};

Line(2)  = {4,5};
Line(3)  = {5,6};
Line(4)  = {6,7};
Line(5)  = {7,4};

Line(6)  = {5,10};
Line(7)  = {10,11};

Line(8)  = {18,19};
Line(9)  = {19,20};
Line(10)  = {20,21};
Line(11)  = {21,18};

Line(12)  = {13,12};
Line(13)  = {12,1};

Line(14)  = {22,23};
Line(15)  = {23,24};
Line(16)  = {24,25};
Line(17)  = {25,22};

Line(18)  = {6,19};
Line(19)  = {7,18};
Line(20)  = {20,23};
Line(21)  = {21,22};

Circle(22) = {10,1,12};
Circle(23) = {11,1,13};

Line Loop(30) = {2,3,4,5};       // Ind
Line Loop(31) = {8,9,10,11};     // Ind 1
Line Loop(32) = {14,15,16,17};   // Ind 2

Line Loop(33) = {1,-5,19,-11,21,-17,-16,-15,-20,-9,-18,-3,6,22,13}; // Air

Line Loop(34) = {-4,18,-8,-19};   // Glue 1
Line Loop(35) = {-10,20,-14,-21}; // Glue 2

Line Loop(36) = {7,23,12,-22};    // Air Inf

/* Define Discretization for Lines */

Transfinite Line{5,3} = nbpt_z ;

Transfinite Line{17,15,11,9} = 2*nbpt_z ;
Transfinite Line{16,14,10,8,4,2} = nbpt_r ;
Transfinite Line{21,20,19,18} = nbpt_glue ;

// Transfinite Line{7,-12} = nbpt_r_inf  Using Progression 0.5;
// Transfinite Line{22,23} = nbpt_circum_inf;

//Transfinite Line{1} = nbpt_r_air;
//Transfinite Line{6} = nbpt_rext_air Using Progression 0.25;
//Transfinite Line{-13} = nbpt_z_air Using Progression 0.25;

// Define Surfaces
Plane Surface(133) = {33}; // Air
Plane Surface(136) = {36}; // Air Inf
Plane Surface(134) = {34}; // Glue 1
Plane Surface(135) = {35}; // Glue 2
Plane Surface(130) = {30}; // Ind
Plane Surface(131) = {31}; // Ind 1
Plane Surface(132) = {32}; // Ind 2


Transfinite Surface{130} = {4,5,6,7}; 
Transfinite Surface{131} = {18,19,20,21}; 
Transfinite Surface{132} = {22,23,24,25}; 

Transfinite Surface{134} = {7,6,19,18};
Transfinite Surface{135} = {21,20,23,22};

//Transfinite Surface{136} = {10,11,13,12};

Recombine Surface {130,131,132,134,135};

Physical Line(100) = {1,2,6,7};      // Axe Or
Physical Line(101) = {23};		// Infini
Physical Line(102) = {-13,-12};		// Axe Oz
 
Physical Surface(200) = {130}; // Inducteur
Physical Surface(201) = {131}; // Inducteur 1
Physical Surface(202) = {132}; // Inducteur 2
Physical Surface(203) = {134,135}; // Glue
Physical Surface(204) = {133}; // Air
Physical Surface(205) = {136}; // Air Inf


