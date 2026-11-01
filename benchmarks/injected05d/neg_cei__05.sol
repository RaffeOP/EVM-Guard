pragma solidity 0.5.12;

contract Treasury6985 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public balances;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        supply += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        balances[msg.sender] -= amount;
        supply -= amount;
        (bool ok, ) = msg.sender.call.value(amount)("");
        require(ok);
    }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }

    function ownerOf_() public view returns (address) { return owner; }
}
