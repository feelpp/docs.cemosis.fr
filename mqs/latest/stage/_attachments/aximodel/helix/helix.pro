/* -------------------------------------------------------------------
     File "CoreMassive.pro"

     This file defines the problem dependent data structures for the
     dynamic core-inductor problem.
     
     To compute the solution: getdp CoreMassive -msh core.msh -solve MagDyn_av_Axi
     To compute post-results: getdp CoreMassive -msh core.msh -pos Map_a
                           or getdp CoreMassive -msh core.msh -pos U_av
     ------------------------------------------------------------------- */

  Group {

    Ind        = Region[ 200 ];
    Ind1       = Region[ 201 ];
    Ind2       = Region[ 202 ];
    Glue       = Region[ 203 ];
    Air        = Region[ 204 ];
    AirInf     = Region[ 205 ];

    SurfaceAxe  = Region[ 102 ];
    SurfaceGInf = Region[ 101 ];
    SurfaceSym  = Region[ 100 ];

    
    
    // Domains for Electromagnetics Problems 

    //DomainCC_Mag = Region[ {Glue, Air, AirInf} ] ;
    DomainCC_Mag = Region[ {Glue, Ind1, Ind2, Air, AirInf} ] ;
    /* Massive inductor (Ind), in DomainC_Mag */
    DomainB_Mag  = Region[ {} ] ;

    // if Static analysis
    //DomainS_Mag  = Region[ {Ind, Ind1, Ind2} ] ;
    //DomainC_Mag  = Region[ {} ] ;
    // if transient analysis
    DomainS_Mag  = Region[ {} ] ;
    DomainC_Mag  = Region[ {Ind}]; //, Ind1, Ind2} ] ;


    DomainInf = Region[ {AirInf} ] ;
    Val_Rint = 400.e-3 ;  
    Val_Rext = 500.e-3 ;


    Domain_Mag = Region[ {DomainCC_Mag, DomainC_Mag, DomainS_Mag} ] ;
  }

  Function {
    Factor [ Region[{DomainC_Mag} ] ] = 1.0/(2.0*Pi); //in case of Transient Axi
    mu0 = 4.e-7 * Pi ;

    nu [ Region[{Air, Ind, Ind1, Ind2, Glue, AirInf} ] ]  = 1. / mu0 ;
    
    sigma [ Ind ] = 5.9e7;
    // sigma [ Ind1 ] = 5.9e7;
    // sigma [ Ind2 ] = 5.9e7;
    
    //
    
    Surface[ Region[{Ind}] ] = 25.e-3*50e-3;
    //Surface[ Region[{Ind1}] ] = 25.e-3*50e-3;
    //Surface[ Region[{Ind2}] ] = 25.e-3*50e-3;
    
    // Aubert's Value
    Current[ Region[{Ind}] ] = -134145.81; 
    //Current[ Region[{Ind1}] ] = -134145.81;
    //Current[ Region[{Ind2}] ] = -134145.81;

    Distribution[ Region[{Ind}] ] = Current[]*75.e-3 / ((75.e-3 * Log[100./75.] * 50.e-3) * X[]);
    //Distribution[ Region[{Ind1}] ] = Current[]*75.e-3 / ((75.e-3 * Log[100./75.] * 50.e-3) * X[]);
    //Distribution[ Region[{Ind2}] ] = Current[]*75.e-3 / ((75.e-3 * Log[100./75.] * 50.e-3) * X[]);
    
    //Parameters for Transient Analysis
    Nbr_Time_Steps = 200;
    TC = 1.0;
    Mag_time0 = 0;
    Mag_TimeMax = TC;
    Mag_DTime[] = (Mag_TimeMax-Mag_time0)/Nbr_Time_Steps;
    
    Mag_Theta[] = 0.5;
    
    Tau = 0.1*TC;
    Time_Fct_Ramp[] = ($Time < Tau) ? $Time/Tau  : 1;
    Time_Fct_Step[] = ($Time >= 0) ? 1 : 0;
    Time_Fct_Creneau[] = ($Time <= 0.5*TC) ? Time_Fct_Ramp[] : 0;

  }

  Constraint {

    { Name MagneticVectorPotential_Axi ; Type Assign;
      Case {
        { Region SurfaceAxe  ; Value 0. ; }
        { Region SurfaceGInf ; Value 0. ; }
      }
    }

    Val_U_ = 1 / (2 * Pi); // 2 Pi since we ...

    { Name Voltage_Axi ;
      Case {
        // To use if transient analysis with U(t)
        // { Region Region[ {Ind,Ind1, Ind2} ] ; Value Val_U_; TimeFunction Time_Fct_Ramp[];}
        { Region Region[ {Ind} ] ; Value Val_U_; TimeFunction Time_Fct_Creneau[];}
        // To use if transient analysis with U step function
        //{ Region Region[ {Ind,Ind1, Ind2} ]; Value Val_U_;}
       }
    }

    // Set to Zero if transient analysis else to bitter distribution
    { Name SourceCurrentDensityZ ;
      Case {
        // To use if Static analysis
	// { Region DomainS_Mag ; Value Distribution[] ; }
	{ Region DomainS_Mag ; Value 0 ; }
      }
    }
  }


  Include "Jacobian_Lib.pro"
  Include "Integration_Lib.pro"

  Include "MagDyn_av_Axi.pro"
  Include "MagSta_a_Axi.pro"
  //Include "Heat_Axi.pro"

  PostOperation Map_av UsingPost MagDyn_t_av_Axi {
    Print[ az, OnElementsOf Domain_Mag, File "test_MagDyn_a.pos", TimeStep {1:Nbr_Time_Steps}] ;
    Print[ V, OnElementsOf DomainC_Mag, File "test_MagDyn_V.pos", TimeStep {1:Nbr_Time_Steps}] ;
    Print[ jz, OnElementsOf DomainC_Mag, File "test_MagDyn_j.pos", TimeStep {1:Nbr_Time_Steps}] ;
    Print[ jf, OnElementsOf DomainC_Mag, File "test_MagDyn_jf.pos", TimeStep {1:Nbr_Time_Steps}] ;
    Print[ jc, OnElementsOf DomainC_Mag, File "test_MagDyn_jc.pos", TimeStep {1:Nbr_Time_Steps}] ;
    Print[ roj2, OnElementsOf DomainC_Mag, File "test_MagDyn_Joules.pos", TimeStep {1:Nbr_Time_Steps}] ;
    Print[ b, OnLine {{1.e-06,0,0}{250.e-3, 0, 0}} {50}, File "test_MagDyn_b.pos" , Format Gnuplot, TimeStep {Nbr_Time_Steps:Nbr_Time_Steps}] ;
    Print[ b, OnPoint {0,0,0}, File "test_MagDyn_bz.pos" , Format TimeTable] ;
  }

  PostOperation U_av UsingPost MagDyn_t_av_Axi {
    Print[ R, OnRegion #{Ind},File "test_MagDyn_R.pos" , Format Table, TimeStep {Nbr_Time_Steps:Nbr_Time_Steps}] ;
    Print[ U, OnRegion #{Ind},File "test_MagDyn_U.pos" , Format TimeTable] ;
    Print[ I, OnRegion #{Ind},File "test_MagDyn_I.pos" , Format TimeTable] ;
  }

/*********
  PostOperation U_av UsingPost MagDyn_t_av_Axi {
    Print[ R, OnRegion #{Ind, Ind1, Ind2},File "test_MagDyn_R.pos" , Format Table, TimeStep {Nbr_Time_Steps:Nbr_Time_Steps}] ;
    Print[ U, OnRegion #{Ind, Ind1, Ind2},File "test_MagDyn_U.pos" , Format TimeTable] ;
    Print[ I, OnRegion #{Ind, Ind1, Ind2},File "test_MagDyn_I.pos" , Format TimeTable] ;
  }
*********/

  PostOperation Map_a UsingPost MagSta_a_Axi {
    Print[ a_theta, OnElementsOf Domain_Mag, File "test_magsta_a.pos"] ;
    Print[ j_theta, OnElementsOf DomainS_Mag, File "test_magsta_j.pos"] ;
    Print[ j_source, OnElementsOf DomainS_Mag, File "test_magsta_js.pos"] ;
    Print[ roj2, OnElementsOf DomainS_Mag, File "test_magsta_Joules.pos"] ;
    Print[j_source, OnLine {{75.e-3,0,0}{100.e-3,0,0}}{10}, File "test_magsta_j2.pos", Format Gnuplot];
    Print[j_theta, OnLine {{75.e-3,0,0}{100.e-3,0,0}}{10}, File "test_magsta_jt2.pos", Format Gnuplot];
    Print[ b, OnLine {{1.e-06,0,0}{250.e-3, 0, 0}} {50}, File "test_magsta_b.pos" , Format Gnuplot ] ;
  }
