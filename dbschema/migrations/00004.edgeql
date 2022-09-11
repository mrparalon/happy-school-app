CREATE MIGRATION m1zudhxixvrblvcqtczcsizb662lwfscdr3pzbl2asso2y3edt34hq
    ONTO m1cifb5rdmxonibqz74mos773uouxfrysm4d2jf4k3sumsdtbladla
{
  ALTER TYPE default::User {
      ALTER LINK identity {
          RESET OPTIONALITY;
      };
  };
};
