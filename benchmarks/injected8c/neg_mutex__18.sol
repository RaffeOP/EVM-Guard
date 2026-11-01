pragma solidity 0.8.20;

contract Fund6117 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public shares;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        supply += msg.value;
    }
    bool private locked;

    function withdraw(uint256 amount) public {
        require(!locked);
        locked = true;
        require(shares[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok);
        shares[msg.sender] -= amount;
        supply -= amount;
        locked = false;
    }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }

    function ownerOf_() public view returns (address) { return owner; }
}
