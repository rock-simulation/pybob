import execute

def get_ruby_verison():
    out, err, r = execute.do(["ruby -r rbconfig -e \"print RbConfig::CONFIG['MAJOR']\""])
    major = execute.decode(out)[0]
    out, err, r = execute.do(["ruby -r rbconfig -e \"print RbConfig::CONFIG['MINOR']\""])
    minor = execute.decode(out)[0]
    return (major,minor)

def get_ruby_archdir():
    out, err, r = execute.do(["ruby -r rbconfig -e \"print RbConfig::CONFIG['archdir']\""])
    return execute.decode(out).split("/")[-1]
