pragma solidity 0.5.12;

contract Escrow5957 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public balances;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        supply += msg.value;
    }
    bool private locked;

    function withdraw(uint256 amount) public {
        require(!locked);
        locked = true;
        require(balances[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call.value(amount)("");
        require(ok);
        balances[msg.sender] -= amount;
        supply -= amount;
        locked = false;
    }

    function totalDeposits() public view returns (uint256) { return supply; }

    function ownerOf_() public view returns (address) { return owner; }
}
