CREATE MIGRATION m1ighgtwvkwnwtvoggscm2hsdh5h4ku5sshbfhtl5z5tdky7j5idtq
    ONTO m14rqksyvduxayjbrqr2rc5he666eklp2aiznukhp5yotjwb2dw3oq
{
  CREATE TYPE default::Review EXTENDING default::CreatedUpdated {
      CREATE REQUIRED LINK reviewed_by: default::Teacher;
      CREATE REQUIRED LINK reviewed_to: default::Student;
      CREATE REQUIRED PROPERTY engagement: std::int32 {
          CREATE CONSTRAINT std::max_value(5);
          CREATE CONSTRAINT std::min_value(1);
      };
      CREATE REQUIRED PROPERTY focus: std::int32 {
          CREATE CONSTRAINT std::max_value(5);
          CREATE CONSTRAINT std::min_value(1);
      };
      CREATE REQUIRED PROPERTY review: std::str;
  };
};
