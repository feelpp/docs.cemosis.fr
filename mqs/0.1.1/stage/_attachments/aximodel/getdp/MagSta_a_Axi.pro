/* -------------------------------------------------------------------
     File "MagSta_a_Axi.pro"

      Magnetostatics - Magnetic vector potential a formulation (Axi)
     ------------------------------------------------------------------- 

     I N P U T
     ---------

     GlobalGroup :  (Extension '_Mag' is for Magnetic problem)
     -----------
     Domain_Mag               Whole magnetic domain
     DomainS_Mag              Inductor regions (Source)

     Function :
     --------
     nu[]                     Magnetic reluctivity

     Constraint :
     ----------
     MagneticVectorPotential_Axi
                              Fixed magnetic vector potential (Axi)
                              (classical boundary condition)
     SourceCurrentDensityY    Fixed source current density (in Y direction)
  */

  Group {
    DefineGroup[ Domain_Mag, DomainS_Mag, DomainC_Mag ] ;
  }

  Function {
    DefineFunction[ nu ] ;
    DefineFunction[ Distribution ] ;
  }

  FunctionSpace {

    // Magnetic vector potential a (b = curl a)
    { Name Hcurl_a_MagSta_Axi ; Type Form1P ;
      BasisFunction {
        // a = a  s
        //      e  e
        { Name se ; NameOfCoef ae ; Function BF_PerpendicularEdge ;
          Support Domain_Mag ; Entity NodesOf[ All ] ; }
      }
      Constraint {
        { NameOfCoef ae ; EntityType NodesOf ;
          NameOfConstraint MagneticVectorPotential_Axi ; }
      }
    }

    // Source current density js (fully fixed space)
    { Name Hregion_j_MagSta_Axi ; Type Vector ;
      BasisFunction {
        { Name sr ; NameOfCoef jsr ; Function BF_NodeZ ;
          Support DomainS_Mag ; Entity NodesOf[DomainS_Mag ]; }
      }
      Constraint {
        { NameOfCoef jsr ; EntityType NodesOf ;
          NameOfConstraint SourceCurrentDensityZ ; }
      }
    }

//     // for constant Current Densities
//     { Name Hregion_j_MagSta_Axi ; Type Vector ;
//       BasisFunction {
//         { Name sr ; NameOfCoef jsr ; Function BF_RegionZ ;
//           Support DomainS_Mag ; Entity DomainS_Mag; }
//       }
//       Constraint {
//         { NameOfCoef jsr ; EntityType Region ;
//           NameOfConstraint SourceCurrentDensityZ ; }
//       }
//     }

  }


  Formulation {
    { Name Magnetostatics_a_Axi ; Type FemEquation ;
      Quantity {
        { Name a  ; Type Local ; NameOfSpace Hcurl_a_MagSta_Axi ; }
        { Name js ; Type Local ; NameOfSpace Hregion_j_MagSta_Axi ; }
      }
      Equation {
        Galerkin { [ nu[] * Dof{d a} , {d a} ]  ; In Domain_Mag ;
                   Jacobian VolAxi ; Integration CurlCurl ; }
        Galerkin { [ - Dof{js} , {a} ] ; In DomainS_Mag ;
                   Jacobian VolAxi ; Integration CurlCurl ; }
        //Galerkin { [ - Vector[0,0,Distribution[]] , {a} ] ; In DomainS_Mag ; //just to check
        //           Jacobian VolAxi ; Integration CurlCurl ; }
      }
    }
  }


  Resolution {
    { Name MagSta_a_Axi ;
      System {
        { Name Sys_Mag ; NameOfFormulation Magnetostatics_a_Axi ; }
      }
      Operation {
        Generate Sys_Mag ; Solve Sys_Mag ; SaveSolution Sys_Mag ;
      }
    }
  }


  PostProcessing {
    { Name MagSta_a_Axi ; NameOfFormulation Magnetostatics_a_Axi ;
      PostQuantity {
        { Name a  ; Value { Local { [ {a} ]          ; In Domain_Mag ; Jacobian VolAxi ; } } }
        { Name a_theta ; Value { Local { [ CompZ[{a}] ]   ; In Domain_Mag ; Jacobian VolAxi ; } } }
        { Name b  ; Value { Local { [ {d a} ] ; In Domain_Mag ; Jacobian VolAxi ; } } }
        { Name h  ; Value { Local { [ nu[] * {d a} ] ; In Domain_Mag ; Jacobian VolAxi ;} } }
        { Name j_theta  ; Value { Local { [ CompZ[{js}] ] ; In DomainS_Mag ; Jacobian VolAxi ; } } }
        { Name j_source  ; Value { Local { [ Distribution[] ] ; In DomainS_Mag ; Jacobian VolAxi ; } } }
        { Name roj2  ; Value { Local { [ SquNorm[CompZ[{js}]] / sigma[] ] ; In DomainS_Mag ; Jacobian VolAxi ; } } }
      }
    }
  }

